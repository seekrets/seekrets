import re
import os
import sh
import sys
import json
import datetime
try:
    from urllib.parse import urljoin
except:
    from urlparse import urljoin


from . import utils
from . import constants

import git
import giturlparse

# TEST AKIATM9O2ZJBIALM2DCP
# TEST AWsJU1lDU5u83Csw9fZux4UG2JAyg9Odxm/bsHHF


COMMON_EXPRESSIONS = {
    'AWS Access Key ID': re.compile('AKIA[0-9A-Z]{16}'),
}

logger = utils.setup_logger()


def _clone(source, destination):
    logger.info('Cloning %s to %s...', source, destination)
    git.Repo.clone_from(source, destination)


def _pull(repo, branch):
    logger.info('Pulling %s...', branch.name)
    # TODO: Should use this.. but it's weirdly not working
    # repo.remotes.origin.pull()
    sh.git.pull()


def _get_branches(repo):
    logger.info('Retrieving branches...')
    return repo.remotes.origin.fetch()


def _get_branch_name(branch):
    return branch.name.split('/')[1]


def _checkout(repo, branch, branch_name):
    logger.info('Checking out %s...', branch_name)
    repo.git.checkout(branch)


def _get_commits(repo, searched):
    logger.info('Getting all commits...')
    commits = repo.iter_commits()
    return set([c for c in commits if c not in searched])


def _reduce_checked(list1, list2):
    return set([item for item in list1 if item not in list2])


def _set_clone_path(meta):
    return os.path.join(
        constants.CLONED_REPOS_PATH, meta.owner, meta.name)


def _search_commit(branch, meta, commit, diff, search_type='common', strings=None):
    record = {
        'commit_sha': commit.hexsha,
        'commit_date': commit.committed_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
        'committer_email': commit.committer.email,
        'committer_username': commit.committer.name,
        'commit_msg': commit.message,
        'branch': branch.name,
        'repo': meta.name,
        'org': meta.owner,
        'found': [],
    }
    for index, blob in enumerate(diff):
        data = blob.diff.decode('utf-8', errors='replace')
        blob_parts = [meta.href.replace('.git', ''), 'blob', commit.hexsha]
        # TODO: APPEND PATH TO BLOB URL!
        # commit.tree.blobs[index].path
        blob_url = '/'.join(blob_parts)

        if search_type == 'common':
            for key_type, expression in COMMON_EXPRESSIONS.items():
                result = expression.findall(data)
                if result:
                    record['found'].append({
                        'blob_url': blob_url,
                        'strings': result,
                        'type': key_type
                    })
        else:
            result = [s for s in strings if s in data]
            if result:
                record['found'].append({
                    'blob_url': blob_url,
                    'strings': result,
                    'type': 'custom'
                })

    return record


def _search_branches(repo, no_pull, skip_common=False):
    found = []
    searched = []

    for branch in _get_branches(repo):
        logger.info('Searching %s...', branch)

        if not repo.cloned_now and not no_pull:
            _pull(repo, branch)
        branch_name = _get_branch_name(branch)
        _checkout(repo, branch, branch_name)

        commits = _get_commits(repo, searched)
        previous_commit = None
        for commit in commits:
            searched.append(commit)
            if not previous_commit:
                pass
            else:
                if not skip_common:
                    diff = previous_commit.diff(commit, create_patch=True)
                    record = _search_commit(branch, repo.meta, commit, diff)
                    if record.get('found'):
                        found.append(record)
            previous_commit = commit

        logger.info('Searched %s commits.', len(searched))

    return found


def seekrets(repo_url,
             search_list=None,
             skip_common=False,
             no_pull=False,
             verbose=False):
    """Search for a list of strings or secret oriented regex in a repo

    Example output:

    [
        {
            "org": "nir0s"
            "branch": "origin/master",
            "repo": "ghost",
            "committer_username": "nir0s",
            "commit_msg": "Do something",
            "committer_email": "w00t@w00t.com",
            "commit_date": "2015-03-10T18:19:52",
            "commit_sha": "a28004a2651f2d30ba4322f67f5ce951722059e5",
            "found": [
                {
                    "type": "AWS Access Key ID",
                    "blob_url": "https://github.com/nir0s/ghost/blob/.../ghost.py",
                    "strings": [
                        "AKIAJFLYGO6XOVXOXXXX"
                    ]
                }
            ],
        },
        ...
    ]
    """
    meta = giturlparse.parse(repo_url)

    clone_path = _set_clone_path(meta)
    cloned_now = False

    if not os.path.isdir(clone_path):
        _clone(source=repo_url, destination=clone_path)
        cloned_now = True
    repo = git.Repo(clone_path)
    repo.meta = meta
    repo.cloned_now = cloned_now

    results = _search_branches(repo, no_pull)
    print(json.dumps(results, indent=4))
    return results
