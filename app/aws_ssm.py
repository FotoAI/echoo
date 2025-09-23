import os
import boto3
from typing import Dict

def get_ssm_parameters() -> Dict[str, str]:
    """Get parameters from SSM and return as dictionary"""
    env = os.getenv('ENVIRONMENT', 'prod')
    path = f'/echoo'  # Use /echoo as the path
    print(f"Getting SSM parameters for environment: {env}, path: {path}")
    
    try:
        ssm = boto3.client('ssm', 'us-east-2')
        NextToken = '-1'
        params = []
        
        while NextToken:
            if NextToken == '-1':
                NextToken = None
            if NextToken:
                response = ssm.get_parameters_by_path(
                    Path=path, 
                    Recursive=True, 
                    NextToken=NextToken, 
                    WithDecryption=True
                )
            else:
                response = ssm.get_parameters_by_path(
                    Path=path, 
                    Recursive=True, 
                    WithDecryption=True
                )

            NextToken = response.get('NextToken')
            params.extend(response['Parameters'])

        # Convert to dictionary - extract parameter name after the path prefix
        # For /echoo/POSTGRES_USER -> POSTGRES_USER
        ssm_dict = {}
        for param in params:
            param_name = param['Name'].split('/')[-1]  # Get last part after final /
            ssm_dict[param_name] = param['Value']
            
        print(f"Loaded {len(ssm_dict)} parameters from SSM")
        return ssm_dict
    except Exception as e:
        print(f"Warning: Could not fetch SSM parameters: {str(e)}")
        return {}

def set_env(force: bool = False):
    """Set environment variables from SSM with priority over .env"""
    ssm_params = get_ssm_parameters()
    
    # Update environment with SSM parameters (these will take priority)
    for key, value in ssm_params.items():
        os.environ[key] = value
        print(f"Set environment variable: {key}")