===========================
 Community-wide Goal Tools
===========================

To use the tools, run ``tox -e venv --notest`` to create a virtualenv
with all of the dependencies. The tools will then be installed into
``.tox/venv/bin`` and can be run directly from there or via ``tox -e
venv -- COMMAND_NAME``.

import-goal
===========

``import-goal`` can be used to create stories, tasks, and boards in
storyboard for tracking work on completing the goals.

who-helped
==========

``who-helped`` is a tool for looking at the contributor statistics for
a set of patches.

python3-first
=============

``python3-first`` is the parent command for a set of tools for
implementing the `python3-first goal
<https://review.openstack.org/#/c/575933/>`_.

The ``jobs extract`` sub-command reads the Zuul configuration from the
``openstack/project-config`` repository and then for a given
repository and branch prints the set of job definitions that should be
copied into that branch of that project.

.. code-block:: console

   $ git clone git://git.openstack.org/openstack-infra/project-config
   $ git clone git://git.openstack.org/openstack/goal-tools
   $ cd goal-tools
   $ tox -e venv -- python3-first jobs extract --project-config ../project-config \
   openstack-dev/devstack stable/queens

The ``jobs retain`` sub-command reads the same Zuul configuration data
and prints the settings that need to stay in
``openstack/project-config``.

.. code-block:: console

   $ tox -e venv -- python3-first jobs retain --project-config ../project-config \
   openstack-dev/devstack

The ``jobs update`` command will modify the zuul settings in a
repository to include all of the settings shown by ``jobs extract``.

.. code-block:: console

   $ git clone git://git.openstack.org/openstack/oslo.config
   $ cd oslo.config
   $ git checkout -b python3-first
   $ cd ../goal-tools
   $ tox -e venv -- python3-first jobs update --project-config ../project-config \
   ../oslo.config

The ``repos clone`` command will use the project governance data to
find a list of all of the git repositories managed by a project team
and then clone local copies of all of them. This makes it easier to
work on all of the projects for a single team as a batch.

.. code-block:: console

   $ mkdir Oslo
   $ cd goal-tools
   $ tox -e venv -- python3-first repos clone ../Oslo Oslo

Use the ``-v`` option to python3-first to see debug information on
stderr (allowing stdout to be redirected to a file safely).

There are several higher-level wrapper scripts for running these tools
in ``tools/python3-first``.

``do_team.sh`` takes as input a working directory and a team name. It
clones all of the repositories owned by the team and prepares local
branches with patches to import jobs into master and all of the
relevant stable branches.

.. code-block:: console

   $ cd goal-tools
   $ ./tools/python3-first/do_team.sh ../Documentation Documentation

``process_team.sh`` can be used to re-run one stage of the patch
creation process for all of the repos and a single branch.

.. code-block:: console

   $ ./tools/python3-first/process_team.sh ../Documentation Documentation stable/rocky

``do_repo.sh`` creates the branch and patch for a single repository.

.. code-block:: console

   $ ./tools/python3-first/do_repo.sh ../Documentation/openstack/whereto stable/rocky
