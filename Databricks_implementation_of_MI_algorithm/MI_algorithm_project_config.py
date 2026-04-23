# Databricks notebook source
import sys
import os

# Grab username
username = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().apply('user')

# Project conficuration (project_config.json) path
project_config_path = f'/Workspace/Repos//hds_jf_score_cvd_mi/databricks/config/project_config.json'

# Append repos to 
sys.path.append(f"/Workspace/Repos/{username}/")

# Read project config, parse project folder
from hds_functions import read_json_file
project_config = read_json_file(path=project_config_path)
project_name = project_config['project_name']
project_folder = project_config['project_folder'].format(username = username, project_name = project_name)
del read_json_file

# Assign to environment 
os.environ['USERNAME'] = username
os.environ['PROJECT_FOLDER'] = project_folder
os.environ['PROJECT_NAME'] = project_name

# Disable io cache
spark.conf.set("spark.databricks.io.cache.enabled", "false")
