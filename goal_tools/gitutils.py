import logging
import os.path
import subprocess

LOG = logging.getLogger(__name__)

start_dir = os.getcwd()
tools_dir = os.path.join(start_dir, 'tools')


def clone_repo(workdir, repo):
    LOG.info('cloning %s', repo)
    repo_dir = os.path.join(workdir, repo)
    if os.path.exists(repo_dir):
        raise RuntimeError('Found another copy of {} at {}'.format(
            repo, repo_dir))
    subprocess.run(
        [os.path.join(tools_dir, 'clone_repo.sh'),
         '--workspace', workdir,
         repo],
        check=True,
    )
    return os.path.join(workdir, repo)


def git(repo_dir, *args):
    subprocess.run(
        ['git'] + list(args),
        check=True,
        cwd=repo_dir,
    )
