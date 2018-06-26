===========================
 Community-wide Goal Tools
===========================

To use the tools, run ``tox -e venv --notest`` to create a virtualenv
with all of the dependencies. The tools will then be installed into
``.tox/venv/bin`` and can be run directly from there or via ``tox -e
venv -- COMMAND_NAME``.

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

Use the ``-v`` option to python3-first to see debug information on
stderr (allowing stdout to be redirected to a file safely).
