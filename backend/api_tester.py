import requests
import json
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base URL for the API
BASE_URL = 'http://localhost:8000'

# Test data
test_data = {
    'employee': {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'phone': '1234567890',
        'date_of_birth': '1990-01-01',
        'date_of_joining': '2024-01-01',
        'employee_id': 'EMP001',
        'department': 1,
        'designation': 1
    },
    'leave_request': {
        'employee': "2d1e446b-4ea9-4c9d-a586-f2d0d34cb8d9",
        'leave_type': 3,
        'start_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'end_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
        'reason': 'Test leave request'
    },
    'document': {
        'title': 'Test Document',
        'description': 'Test document description',

        'category': 9,
        'status': 'draft'
    }
}

def print_result(endpoint, success, response=None):
    """Print the test result in a formatted way"""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    print(f"\n{endpoint}: {status}")
    if response:
        print(f"Response: {response.status_code}")
        try:
            print(f"Data: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Data: {response.text}")

def test_endpoint(method, endpoint, data=None, headers=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        success = 200 <= response.status_code < 300
        print_result(endpoint, success, response)
        return success, response
    except Exception as e:
        print_result(endpoint, False)
        print(f"Error: {str(e)}")
        return False, None

def test_authentication():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication Endpoints ===")
    
    # Test token obtain
    auth_data = {
        'username': 'genhub',
        'password': 'genhub'
    }
    success, response = test_endpoint('POST', '/api/token/', auth_data)
    
    if success:
        token = response.json().get('access')
        headers = {'Authorization': f'Bearer {token}'}
        return headers
    return None

def test_employee_endpoints(headers):
    """Test employee-related endpoints"""
    print("\n=== Testing Employee Endpoints ===")
    
    # Test departments
    test_endpoint('GET', '/api/employees/departments/', headers=headers)
    test_endpoint('POST', '/api/employees/departments/', 
                 {'name': 'Test Department', 'description': 'Test'}, headers=headers)
    
    # Test designations
    test_endpoint('GET', '/api/employees/designations/', headers=headers)
    test_endpoint('POST', '/api/employees/designations/', 
                 {'title': 'Test Designation', 'description': 'Test', 'department': 1}, headers=headers)
    
    # Test employees
    test_endpoint('GET', '/api/employees/employees/', headers=headers)
    test_endpoint('POST', '/api/employees/employees/', test_data['employee'], headers=headers)

def test_leave_endpoints(headers):
    """Test leave-related endpoints"""
    print("\n=== Testing Leave Endpoints ===")
    
    # Test leave types
    test_endpoint('GET', '/api/leave/leaveType/', headers=headers)
    test_endpoint('POST', '/api/leave/leaveType/', 
                 {'name': 'Test Leave', 'description': 'Test'}, headers=headers)
    
    # Test leave requests
    test_endpoint('GET', '/api/leave/leaveRequest/', headers=headers)
    test_endpoint('POST', '/api/leave/leaveRequest/', test_data['leave_request'], headers=headers)

def test_document_endpoints(headers):
    """Test document-related endpoints"""
    print("\n=== Testing Document Endpoints ===")
    
    # Test document categories
    test_endpoint('GET', '/api/documents/categories/', headers=headers)
    test_endpoint('POST', '/api/documents/categories/', 
                 {'name': 'Test Category', 'description': 'Test'}, headers=headers)
    
    # Test documents
    test_endpoint('GET', '/api/documents/documents/', headers=headers)
    test_endpoint('POST', '/api/documents/documents/', test_data['document'], headers=headers)

def test_boarding_endpoints(headers):
    """Test boarding-related endpoints"""
    print("\n=== Testing Boarding Endpoints ===")
    
    # Test process templates
    test_endpoint('GET', '/api/boarding/process-templates/', headers=headers)
    test_endpoint('POST', '/api/boarding/process-templates/', 
                 {'name': 'Test Process','process_type': 'onboarding', 'description': 'Test'}, headers=headers)
    
    # Test tasks
    test_endpoint('GET', '/api/boarding/tasks/', headers=headers)
    test_endpoint('POST', '/api/boarding/tasks/', 
                                                {
                                                    "name": "Test Task",
                                                    "description": "Test",
                                                    "process" : 1,
                                                    "department" : 15
                                                }
                                                , headers=headers)

def test_analytics_endpoints(headers):
    """Test analytics-related endpoints"""
    print("\n=== Testing Analytics Endpoints ===")
    
    # Test reports
    test_endpoint('GET', '/api/analytics/reports/', headers=headers)
    
    # Test HR metrics
    test_endpoint('GET', '/api/analytics/hr-metrics/', headers=headers)

def main():
    """Main function to run all tests"""
    print("Starting API Tests...")
    
    # Test authentication and get token
    headers = test_authentication()
    if not headers:
        print("Authentication failed. Please check your credentials.")
        return
    
    # Test all endpoints
    test_employee_endpoints(headers)
    test_leave_endpoints(headers)
    test_document_endpoints(headers)
    test_boarding_endpoints(headers)
    test_analytics_endpoints(headers)
    
    print("\nAPI Testing completed!")

if __name__ == '__main__':
    main() 