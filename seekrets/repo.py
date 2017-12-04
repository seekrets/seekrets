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


def _clone(repo_url, repo_path):
    logger.info('Cloning %s to %s...', repo_url, repo_path)
    git.Repo.clone_from(repo_url, repo_path)


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


def _get_commits(repo):
    logger.info('Getting all commits...')
    return repo.iter_commits()


def _reduce_checked(list1, list2):
    return set([item for item in list1 if item not in list2])


def _get_repo_path(meta):
    repo_path = os.path.join(
        constants.CLONED_REPOS_PATH, meta.owner, meta.name)
    return repo_path


def _search_commit(branch, meta, commit, previous_commit, search_type='common', strings=None):
    diff = previous_commit.diff(commit, create_patch=True)
    record = {
        'commit_sha': commit.hexsha,
        'commit_date': commit.committed_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
        'committer_email': commit.committer.email,
        'committer_username': commit.committer.name,
        'commit_msg': commit.message,
        'branch': branch.name,
        'repo': meta.name,
        'org': meta.owner,
        'risks': [],
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
                    record['risks'].append(
                        {'blob_url': blob_url, 'strings': result, 'type': key_type})
        else:
            result = [s for s in strings if s in data]
            if result:
                record['risks'].append(
                    {'blob_url': blob_url, 'strings': result, 'type': 'custom'})

    return record


def _search_branches(repo, cloned_now, search_common=True):
    results = []
    reduction_list = []

    for branch in _get_branches(repo):
        logger.info('Searching %s...', branch)
        if not branch.name == 'origin/master':
            continue
        if not cloned_now:
            _pull(repo, branch)
        branch_name = _get_branch_name(branch)
        _checkout(repo, branch, branch_name)
        commits = _get_commits(repo)
        commits = _reduce_checked(commits, reduction_list)
        # TODO: Move to _seek_commits()
        previous_commit = None
        for commit in commits:
            reduction_list.append(commit)
            if not previous_commit:
                pass
            else:
                if search_common:
                    record = _search_commit(
                        branch, repo.meta, commit, previous_commit)
                    if record.get('risks'):
                        results.append(record)
            previous_commit = commit
        logger.info('Searched %s commits.', len(reduction_list))
    return results


def seekrets(repo_url, search_list=None, search_common=True, verbose=False):
    """Search for a list of strings or secret oriented regex in a repo

    Example output:

    {
        [
            {

                "commit_sha": "b788a889e484d57451944f93e2b65ed425d6bf65",
                "commit_date": "Wed Aug 24 11:11:56 2016",
                "committer_email": "nir36g@gmail.com",
                "committer_username": "nir0s",
                "branch": "slack",
                "repo": "ghost",
                "owner": "nir0s",
                "risks": [
                    { "blob_url": "https://github.com/nir0s/ghost/blob/.../ghost.py", "string": "AKI..." },
                    ...
                ]
            },
        ],
        ...
    }
    """
    meta = giturlparse.parse(repo_url)
    clone = _get_repo_path(meta)
    cloned_now = False
    if not os.path.isdir(clone):
        _clone(repo_url, clone)
        cloned_now = True
    repo = git.Repo(clone)
    repo.meta = meta

    results = _search_branches(repo, cloned_now)
    print(json.dumps(results, indent=4))
    return results
