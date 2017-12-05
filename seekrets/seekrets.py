########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import sys

import click

from . import repo
from . import constants
from .exceptions import SeekretsError


CLICK_CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    token_normalize_func=lambda param: param.lower())

search_string = click.option(
    '-s',
    '--string',
    multiple=True,
    default=[],
    help='String you would like to search for. '
         'This can be passed multiple times')
search_common = click.option(
    '--skip-common',
    default=False,
    help='Whether to search for common patterns as well. Defaults to True')
no_pull = click.option(
    '--no-pull',
    is_flag=True,
    default=False,
    help='Whether to skip pulling changes when the repository already exists')
verbose = click.option('-v', '--verbose', default=False, is_flag=True)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def main():
    pass


@main.command(name='repo')
@click.argument('REPO_URL')
@search_string
@search_common
@no_pull
@verbose
def seekrets_repo(repo_url, string, skip_common, no_pull, verbose):
    """Search a single repository.
    You can add user_name and password. Used seekrets like that:

    "seekrets repo 'https://<user>:<pass>@github.com/cloudify-cosmo/seekrets.git'"
    """
    try:
        repo.seekrets(
            repo_url=repo_url,
            search_list=string,
            skip_common=skip_common,
            no_pull=no_pull,
            verbose=verbose)
    except SeekretsError as ex:
        sys.exit(ex)
