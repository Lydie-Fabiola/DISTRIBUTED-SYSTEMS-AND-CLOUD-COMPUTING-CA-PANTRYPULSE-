import bcrypt

def test_existing_credentials():
    """Test the existing credentials from credentials.doc"""
    print("Testing existing credentials...")
    
    # Test johndoe
    stored_hash_john = "$2b$12$lWpDNbV.sfSepqTOriQUR.ZjY.noL3i6Vz2xQKfeQNVfChy/3.do2"
    password_john = "1234567890"
    
    if bcrypt.checkpw(password_john.encode('utf-8'), stored_hash_john.encode('utf-8')):
        print("SUCCESS: johndoe password verified")
    else:
        print("FAILED: johndoe password verification failed")
    
    # Test janedoe
    stored_hash_jane = "$2b$12$gG8zFHAfjqEk2AKzKK3iZOundTPr7G12PNQovEWeDg1P9EaFMsuQG"
    password_jane = "0987654321"
    
    if bcrypt.checkpw(password_jane.encode('utf-8'), stored_hash_jane.encode('utf-8')):
        print("SUCCESS: janedoe password verified")
    else:
        print("FAILED: janedoe password verification failed")
    
    print("\nCredentials are ready to use!")

if __name__ == '__main__':
    test_existing_credentials()
