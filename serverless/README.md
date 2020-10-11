# Serverless

## Requirements

* Python 3.7
* Serverless CLI: https://serverless.com/framework/docs/getting-started/
* Python Requirements plugin: `sls plugin install -n serverless-python-requirements`

## Create a new function

* Run: 
`serverless create --template aws-python3 --name enrich-country --path enrich-country`

## Static Security Analysis

Run Bandit

```
pip3 install bandit
bandit -r .
```
