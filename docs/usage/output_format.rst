Output Format
=============

The tool generates clean, structured Markdown that includes PR metadata, review comments with context, and code diffs.

Document Structure
------------------

The output consists of:

1. **Header** - Repository and pull request metadata
2. **Comment sections** - One section per review comment
3. **Code context** - Diff hunks showing the relevant code
4. **Comment content** - The actual review comment text

Example Output
--------------

Here's a representative example of the generated Markdown:

.. code-block:: markdown

    # PR Review Comments: octocat/Hello-World #42

    **Pull Request:** [Add new feature](https://github.com/octocat/Hello-World/pull/42)
    **Repository:** octocat/Hello-World
    **Generated:** 2023-12-01 14:30:52 UTC

    ---

    ## Comment #1
    **Author:** @reviewerbot
    **File:** `src/main.py`
    **Line:** 25
    **Created:** 2023-11-30 09:15:22 UTC
    **Updated:** 2023-11-30 09:18:45 UTC

    ### Code Context
    ```diff
    @@ -22,7 +22,8 @@ def process_data(data):
         if not data:
             return None
         
    -    result = data.strip()
    +    # TODO: Add input validation
    +    result = data.strip().lower()
         return result
     ```

    ### Comment
    Consider adding proper input validation here. What happens if `data` is not a string?

    ---

    ## Comment #2  
    **Author:** @security-reviewer
    **File:** `src/utils.py`
    **Line:** 45
    **Created:** 2023-11-30 14:22:10 UTC

    ### Code Context
    ```diff
    @@ -42,6 +42,9 @@ def sanitize_input(user_input):
         """Sanitize user input for safe processing."""
         if not isinstance(user_input, str):
             raise ValueError("Input must be a string")
    +    
    +    # Remove potentially dangerous characters
    +    cleaned = re.sub(r'[<>&]', '', user_input)
         return user_input.strip()
     ```

    ### Comment
    🚨 **Security Issue**: The sanitization logic is not being applied! You're returning the original `user_input` instead of the `cleaned` version.

Metadata Fields
---------------

**Header Information:**
- Pull request title and URL
- Repository name
- Generation timestamp (UTC)

**Per-Comment Information:**  
- Comment author (with @ prefix)
- File path and line number
- Creation and update timestamps
- Resolution status (if applicable)

Code Context
------------

**Diff Format:**
- Uses standard unified diff format with ``@@ ... @@`` headers
- Shows surrounding context lines for better understanding
- Syntax highlighting via ``diff`` code blocks
- Line numbers preserved from the original diff

**Context Rules:**
- Includes sufficient surrounding code for context
- Preserves original indentation and formatting
- Shows both removed (``-``) and added (``+``) lines

Comment Content
---------------

**Formatting:**
- Preserves original Markdown formatting from GitHub
- Maintains line breaks and paragraphs
- Supports GitHub-flavored Markdown features:

  - Code blocks and inline code
  - Links and references
  - Emoji and mentions
  - Task lists and tables

**Special Indicators:**
- Security-related comments may include 🚨 or other emoji
- Resolved comments are excluded by default
- Outdated comments are excluded by default

File Output Options
-------------------

**Stdout (default):**
- Suitable for piping to other tools
- Can be redirected to files using shell redirection

**Auto-generated filename (--output):**
- Format: ``<owner>-<repo>-pr-<number>-<timestamp>.md``
- Example: ``octocat-Hello-World-pr-42-20231201-143052.md``

**Custom filename (--output-file):**
- User-specified path and filename
- Creates parent directories if needed
- Overwrites existing files

Filtering Options
-----------------

**Default behavior:**
- Excludes resolved comments (use ``--include-resolved`` to include)
- Excludes outdated comments (use ``--include-outdated`` to include)
- Shows all unresolved, current comments

**With filtering disabled:**
- ``--include-resolved --include-outdated`` shows all comments
- Useful for comprehensive review archives
- May include significantly more content