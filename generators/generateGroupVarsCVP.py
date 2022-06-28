
def generateGroupVarsCVP(inventory_file, cvpadmin_password):
    variables = {
        "ansible_connection": "network_cli",
        "ansible_http_api_use_ssl": False,
        "ansible_httpapi_validate_certs": False,
        "ansible_user": "ansible",
        "ansible_password": cvpadmin_password,
        "ansible_network_os": "eos",
        "ansible_httpapi_port": 443,
        "ansible_python_interpreter": "$(which python3)"
    }
    return variables

