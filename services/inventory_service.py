import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from ip_validator import IPValidator
 
def validate_ip_and_cidr(ip, cidr):
    validator = IPValidator()
    return validator.validate_ip_in_subnet(ip, cidr) 