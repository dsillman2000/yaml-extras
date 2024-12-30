# Customizations: relative import directory

By default, when using `yaml-extras` to load YAML documents which use `!import` tags, the relative
directory from which imports are resolved will be the current working directory of the running
Python process.

If you would like to override where imports are resolved from, you can call the 
`set_import_relative_dir` method in the `yaml_import` module. There is a corresponding
`get_import_relative_dir` method to retrieve the current setting.

---

::: yaml_extras.yaml_import.set_import_relative_dir
    options:
      show_root_heading: true
      show_root_full_path: false
      heading_level: 3

---

::: yaml_extras.yaml_import.get_import_relative_dir
    options:
      show_root_heading: true
      show_root_full_path: false
      heading_level: 3

