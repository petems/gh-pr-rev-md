Configuration File
==================

``gh-pr-rev-md`` follows the XDG Base Directory Specification for configuration files.

File Locations
--------------

**User configuration file (recommended):**

- Linux/macOS: ``~/.config/gh-pr-rev-md/config.yaml``
- Windows: ``%APPDATA%\gh-pr-rev-md\config.yaml``
- Custom XDG path: ``$XDG_CONFIG_HOME/gh-pr-rev-md/config.yaml``

**System-wide configuration files (optional):**

- ``/etc/xdg/gh-pr-rev-md/config.yaml``
- Other directories in ``$XDG_CONFIG_DIRS``

**Search order:**
1. User config directory (highest precedence)
2. System config directories
3. Built-in defaults (lowest precedence)

Interactive Setup
-----------------

The easiest way to create a configuration file is using the interactive setup::

    gh-pr-rev-md --config-set

This will:

1. Prompt for your GitHub token
2. Ask about default include/exclude preferences
3. Set up output preferences
4. Create the config file in the appropriate location
5. Open the GitHub token creation page if needed

Configuration Format
--------------------

The configuration file uses YAML format. Here's a complete example:

.. code-block:: yaml

    # ~/.config/gh-pr-rev-md/config.yaml
    
    # GitHub personal access token
    token: "ghp_your_github_token_here"
    
    # Include resolved review comments (default: false)
    include_resolved: true
    
    # Include outdated review comments (default: false) 
    include_outdated: false
    
    # Save to auto-generated filename instead of stdout (default: false)
    output: true
    
    # Save to specific file path (overrides 'output' if set)
    output_file: "/path/to/custom/review-file.md"

Configuration Keys
------------------

``token``
~~~~~~~~~

**Type:** String  
**Description:** GitHub personal access token for API authentication  
**Environment equivalent:** ``GITHUB_TOKEN``  
**CLI equivalent:** ``--token``

**Example:**
.. code-block:: yaml

    token: "ghp_1234567890abcdef1234567890abcdef12345678"

**Security note:** Ensure this file has appropriate permissions (600) to protect your token.

``include_resolved``
~~~~~~~~~~~~~~~~~~~~

**Type:** Boolean  
**Description:** Whether to include resolved review comments  
**Default:** ``false``  
**CLI equivalent:** ``--include-resolved``

**Example:**
.. code-block:: yaml

    include_resolved: true

``include_outdated``
~~~~~~~~~~~~~~~~~~~~

**Type:** Boolean  
**Description:** Whether to include outdated review comments (from previous diff versions)  
**Default:** ``false``  
**CLI equivalent:** ``--include-outdated``

**Example:**
.. code-block:: yaml

    include_outdated: false

``output``
~~~~~~~~~~

**Type:** Boolean  
**Description:** Save to auto-generated filename instead of printing to stdout  
**Default:** ``false``  
**CLI equivalent:** ``--output`` / ``-o``

**Example:**
.. code-block:: yaml

    output: true

**Auto-generated filename format:** ``<owner>-<repo>-pr-<number>-<timestamp>.md``

``output_file``
~~~~~~~~~~~~~~~

**Type:** String  
**Description:** Save to specific file path (overrides ``output`` setting)  
**Default:** Not set  
**CLI equivalent:** ``--output-file``

**Example:**
.. code-block:: yaml

    output_file: "~/Documents/pr-reviews/current-review.md"

**Note:** If both ``output`` and ``output_file`` are set, ``output_file`` takes precedence.

File Permissions
----------------

**Recommended permissions:**
::

    chmod 600 ~/.config/gh-pr-rev-md/config.yaml

This ensures only you can read the configuration file (important for protecting your GitHub token).

**Directory creation:**
The tool will automatically create the configuration directory if it doesn't exist when using ``--config-set``.

Configuration Examples
----------------------

**Minimal configuration (token only):**
.. code-block:: yaml

    token: "ghp_your_token_here"

**Development-friendly configuration:**
.. code-block:: yaml

    token: "ghp_your_token_here"
    include_resolved: true
    include_outdated: true
    output: true

**Custom output path:**
.. code-block:: yaml

    token: "ghp_your_token_here"
    output_file: "~/work/current-pr-review.md"

**Archive configuration:**
.. code-block:: yaml

    token: "ghp_your_token_here"
    include_resolved: true
    include_outdated: true
    output_file: "~/archives/pr-reviews/%(repo)s-pr-%(number)s-%(date)s.md"

**Note:** The ``output_file`` path in the last example shows planned template variables that may be supported in future versions.

Troubleshooting
---------------

**Config file not found:**
- Use ``--config-set`` to create one
- Check file permissions and path
- Verify XDG directories are set correctly

**Token not working:**
- Ensure token has correct scopes (``repo``, ``read:org``)
- Check token hasn't expired
- Verify token is correctly formatted (starts with ``ghp_``)

**YAML syntax errors:**
- Validate YAML syntax with online tools
- Check indentation (use spaces, not tabs)
- Ensure strings with special characters are quoted

**File permissions:**
- Ensure config file is readable: ``ls -la ~/.config/gh-pr-rev-md/``
- Fix permissions: ``chmod 600 ~/.config/gh-pr-rev-md/config.yaml``