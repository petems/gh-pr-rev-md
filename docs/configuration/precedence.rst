Configuration Precedence
========================

Configuration values are applied in the following order of precedence (highest to lowest):

1. **Command-line arguments** (highest priority)
2. **Environment variables**  
3. **XDG configuration file**
4. **Default values** (lowest priority)

When a configuration value is set in multiple places, the higher priority source takes precedence.

Precedence Examples
-------------------

**GitHub Token:**

1. ``--token`` command-line argument
2. ``GITHUB_TOKEN`` environment variable
3. ``token`` in config file
4. No token (unauthenticated, with rate limits)

**Include Resolved Comments:**

1. ``--include-resolved`` / ``--no-include-resolved`` flags
2. No environment variable equivalent
3. ``include_resolved: true/false`` in config file  
4. ``false`` (default: exclude resolved comments)

**Output Settings:**

1. ``--output`` / ``--output-file`` command-line arguments
2. No environment variable equivalent
3. ``output: true`` or ``output_file: path`` in config file
4. Print to stdout (default)

Configuration Matrix
--------------------

+-------------------+------------------+--------------------+-----------------+
| Setting           | CLI Argument     | Environment Var    | Config File Key |
+===================+==================+====================+=================+
| GitHub Token      | ``--token``      | ``GITHUB_TOKEN``   | ``token``       |
+-------------------+------------------+--------------------+-----------------+
| Include Resolved  | ``--include-``   | *(none)*           | ``include_``    |
|                   | ``resolved``     |                    | ``resolved``    |
+-------------------+------------------+--------------------+-----------------+
| Include Outdated  | ``--include-``   | *(none)*           | ``include_``    |
|                   | ``outdated``     |                    | ``outdated``    |
+-------------------+------------------+--------------------+-----------------+
| Auto Output       | ``--output``     | *(none)*           | ``output``      |
+-------------------+------------------+--------------------+-----------------+
| Output File       | ``--output-``    | *(none)*           | ``output_``     |
|                   | ``file``         |                    | ``file``        |
+-------------------+------------------+--------------------+-----------------+

Practical Examples
------------------

**Example 1: Token from multiple sources**

Config file (``~/.config/gh-pr-rev-md/config.yaml``)::

    token: "ghp_config_token"

Environment variable::

    export GITHUB_TOKEN="ghp_env_token"

Command line::

    gh-pr-rev-md --token ghp_cli_token https://github.com/owner/repo/pull/123

**Result:** Uses ``ghp_cli_token`` (command-line has highest precedence)

**Example 2: Mixed configuration sources**

Config file::

    include_resolved: true
    output: true

Command line::

    gh-pr-rev-md --include-outdated https://github.com/owner/repo/pull/123

**Result:** 
- Includes resolved comments (from config file)
- Includes outdated comments (from command line)  
- Saves to auto-generated file (from config file)

**Example 3: Environment variable override**

Config file::

    token: "ghp_old_token"

Environment variable::

    export GITHUB_TOKEN="ghp_new_token"

Command line::

    gh-pr-rev-md https://github.com/owner/repo/pull/123

**Result:** Uses ``ghp_new_token`` (environment variable overrides config file)

Checking Current Configuration
------------------------------

To see what configuration is being used, you can:

1. Run with ``--help`` to see default values
2. Check your config file location with ``--config-set``
3. Test with different PR URLs to see which token is being used (rate limits will differ)

**Note:** The tool does not currently provide a ``--show-config`` command, but this may be added in future versions.