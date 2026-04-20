__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# pylint: disable=unused-import

import os
from collections import OrderedDict
from shutil import copyfile
from typing import Any


def ensure_documents_in_folder(
        document_paths: dict[str, Any],
        target_folder: str,
        folder_alias: 'OrderedDict[str, str]') -> dict[str, Any]:
    """
        Ensure that files referenced by `document_paths` exist in `target_folder`, copying them from aliased source locations when necessary, and return a mapping from resolved target file paths to the original metadata values.
        
        Parameters:
            document_paths (dict[str, Any]): Mapping whose keys are source file paths (strings) and values are arbitrary metadata associated with each document.
            target_folder (str): Destination directory where documents must be present.
            folder_alias (OrderedDict[str, str]): Ordered mapping of path prefixes to replacement prefixes used to locate source files when the original path is not directly available. Keys are path aliases to match at the start of an input path; values are the corresponding replacement base paths.
        
        Returns:
            dict[str, Any]: A mapping from the actual file paths in `target_folder` (after ensuring/copying) to the original metadata values from `document_paths`.
        """

    updated_paths = {}

    for path in document_paths:
        name_only = os.path.basename(path)
        target_path = os.path.join(target_folder, name_only)
        if os.path.isfile(target_path):
            updated_paths[target_path] = document_paths[path]
            continue

        for alias in folder_alias:
            if not path.startswith(alias):
                continue
            src_path = path.replace(alias, folder_alias[alias])
            if not os.path.isfile(src_path):
                continue
            copyfile(src_path, target_path)
            updated_paths[target_path] = document_paths[path]
            break

    return updated_paths
