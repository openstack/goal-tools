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

Setup
-----

To set up a workspace to use the python3-first tools::

  $ mkdir python3-first
  $ cd python3-first
  $ git clone git://git.openstack.org/openstack-infra/project-config
  $ git clone git://git.openstack.org/openstack-infra/openstack-zuul-jobs
  $ git clone git://git.openstack.org/openstack-infra/zuul-jobs
  $ git clone git://git.openstack.org/openstack/goal-tools
  $ mkdir Output

Preparing Patches
-----------------

To prepare the patches for one team, use ``do_team.sh``::

  $ cd goal-tools
  $ ./tools/python3-first/do_team.sh ../Output Documentation

The script will create a subdirectory in the output location using the
team name, clone all of the repositories owned by the team, then
process each one to create a patch for each branch that needs to have
job settings imported.

It will also create a log file in the output directory called
``do_team.TIMESTAMP.log`` (where "TIMESTAMP" is replaced with a real
timestamp. The log file should show all of the work done, including
the diffs for all of the patches created.

::

  $ ls -1 ../Output/Documentation/
  do_team.2018-08-04T08:15:29-04:00.log
  master
  ocata
  openstack
  pike
  queens

Proposing Patches
-----------------

Review the log file created by ``do_team.sh`` before proposing the
patches to ensure that there are no extraneous changes (the YAML
parser does not produce exactly the same format output as input, and
we have seen a couple of cases where it introduces errors by changing
the indentation level incorrectly).

Then use ``propose.sh`` to submit the patches::

  $ ./tools/python3-first/propose.sh ../Output Documentation

The script will provide a list of all of the patches to be proposed
and a count, then wait for you to press ``<Return>``. After you do, it
will submit all of the patches to gerrit.

The project-config patch
------------------------

``do_team.sh`` will trigger the script to create the patch to remove
the settings from ``openstack-infra/project-config`` for all of the
repos for a team. ``propose.sh`` will not submit the patch, though,
because we do not want it to accidentally be approved before the jobs
are added in each repository. You should propose it early and mark it
as a work-in-progress by setting the Workflow flag to -1 so teams can
use it while reviewing the other patches.

::

  $ cd ../Output/Documentation/openstack-infra/project-config
  $ git review

Tools
-----

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

``do_team.sh`` takes as input a goal URL, a working directory and a
team name. It clones all of the repositories owned by the team and
prepares local branches with patches to import jobs into master and
all of the relevant stable branches.

.. code-block:: console

   $ cd goal-tools
   $ ./tools/python3-first/do_team.sh ../Py3FirstGoalWork Documentation

``process_team.sh`` can be used to re-run one stage of the patch
creation process for all of the repos and a single branch.

.. code-block:: console

   $ ./tools/python3-first/process_team.sh ../Py3FirstGoalWork Documentation stable/rocky

``do_repo.sh`` creates the branch and patch for a single repository.

.. code-block:: console

   $ ./tools/python3-first/do_repo.sh ../Py3FirstGoalWork/openstack/whereto stable/rocky

After all of the patches for a team are prepared locally, they can be
submitted for review using ``propose.sh``.

.. code-block:: console

   $ ./tools/python3-first/propose.sh ../Py3FirstGoalWork Documentation
