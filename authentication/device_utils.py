"""
Device Fingerprinting Utility
Generates unique device fingerprints based on User-Agent and other headers.
"""

import hashlib
from user_agents import parse


def generate_device_fingerprint(user_agent, ip_address):
    """
    Generate a unique fingerprint for a device.
    
    Args:
        user_agent (str): User-Agent string from request headers
        ip_address (str): IP address of the device
    
    Returns:
        str: SHA256 hash representing device fingerprint
    """
    # Combine unique device characteristics
    fingerprint_string = f"{user_agent}|{ip_address}"
    
    # Generate SHA256 hash
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()


def parse_user_agent(user_agent_string):
    """
    Parse User-Agent string to extract device information.
    
    Args:
        user_agent_string (str): User-Agent string from request headers
    
    Returns:
        dict: Parsed device information including browser, OS, device type
    """
    user_agent = parse(user_agent_string)
    
    return {
        'device_type': get_device_type(user_agent),
        'browser': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string,
        'os': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'device_brand': user_agent.device.brand or '',
        'device_model': user_agent.device.model or '',
    }


def get_device_type(user_agent):
    """
    Determine device type from parsed User-Agent.
    
    Args:
        user_agent: Parsed user agent object
    
    Returns:
        str: 'mobile', 'tablet', or 'desktop'
    """
    if user_agent.is_mobile:
        return 'mobile'
    elif user_agent.is_tablet:
        return 'tablet'
    else:
        return 'desktop'


def generate_device_name(device_info):
    """
    Generate a user-friendly device name.
    
    Args:
        device_info (dict): Parsed device information
    
    Returns:
        str: User-friendly device name (e.g., "Chrome on Windows", "Safari on iPhone")
    """
    browser = device_info.get('browser', 'Unknown Browser')
    os = device_info.get('os', 'Unknown OS')
    device_type = device_info.get('device_type', 'desktop')
    
    if device_type == 'mobile':
        brand = device_info.get('device_brand', '')
        model = device_info.get('device_model', '')
        if brand and model:
            return f"{browser} on {brand} {model}"
        return f"{browser} on {os}"
    elif device_type == 'tablet':
        return f"{browser} on {os} Tablet"
    else:
        return f"{browser} on {os}"


def get_client_ip(request):
    """
    Extract client IP address from request, handling proxies.
    
    Args:
        request: Django request object
    
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP if multiple are present
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info_from_request(request):
    """
    Extract complete device information from Django request.
    
    Args:
        request: Django request object
    
    Returns:
        dict: Complete device information including fingerprint
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    
    # Parse user agent
    device_info = parse_user_agent(user_agent_string)
    
    # Generate fingerprint
    fingerprint = generate_device_fingerprint(user_agent_string, ip_address)
    
    # Generate friendly name
    device_name = generate_device_name(device_info)
    
    return {
        'device_fingerprint': fingerprint,
        'device_name': device_name,
        'device_type': device_info['device_type'],
        'browser': device_info['browser'],
        'browser_version': device_info['browser_version'],
        'os': device_info['os'],
        'os_version': device_info['os_version'],
        'ip_address': ip_address,
        'user_agent': user_agent_string,
    }


def is_new_device(user, device_fingerprint):
    """
    Check if this is a new device for the user.
    
    Args:
        user: User instance
        device_fingerprint (str): Device fingerprint hash
    
    Returns:
        bool: True if new device, False if existing
    """
    from authentication.models import Device
    return not Device.objects.filter(
        user=user,
        device_fingerprint=device_fingerprint
    ).exists()
