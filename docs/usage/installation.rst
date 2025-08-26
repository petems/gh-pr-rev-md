Installation
============

Requirements
------------

* Python >= 3.9

Try it out (without installing)
-------------------------------

Run the tool directly without installation using ``uvx``::

    uvx gh-pr-rev-md https://github.com/octocat/Hello-World/pull/42

``uvx`` automatically creates a temporary environment, installs the tool, runs it, and cleans up.

Installation Methods
--------------------

Recommended: Install as a global tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install using ``uv tool install`` (recommended for CLI tools)::

    uv tool install gh-pr-rev-md

This installs ``gh-pr-rev-md`` into a dedicated environment and adds it to your PATH.

Alternative: Install into a virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    uv pip install gh-pr-rev-md

Other installation methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

With pipx::

    pipx install gh-pr-rev-md

Or with pip::

    python -m pip install gh-pr-rev-md

Verification
------------

After installation, verify that the tool is working::

    gh-pr-rev-md --help

You should see the help text for the command-line interface.