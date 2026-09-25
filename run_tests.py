import ast
import sys

# Test 1: AST parse
try:
    code = open(r'D:/project/chatly/cogs/verification.py', encoding='utf-8').read()
    ast.parse(code)
    print("Test 1: AST parse - PASSED")
except SyntaxError as e:
    print(f"Test 1: AST parse - FAILED: {e}")

# Test 2: Import dependencies
try:
    import discord
    print("Test 2: Discord API import - PASSED")
except ImportError as e:
    print(f"Test 2: Discord API import - FAILED: {e}")

# Test 3: Import the cog module
try:
    sys.path.insert(0, r'D:/project/chatly')
    import cogs.verification as verification_cog
    print("Test 3: Import cogs.verification - PASSED")
except ImportError as e:
    print(f"Test 3: Import cogs.verification - FAILED: {e}")

# Test 4: Check that all functions and classes are defined
try:
    members = [name for name in dir(verification_cog) if not name.startswith('_')]
    print(f"Test 4a: Found {len(members)} public members")
    
    # Check for verification commands
    expected_commands = ['setup_sus_verification', 'manual_verify', 'manual_unverify']
    found_commands = [cmd for cmd in expected_commands if hasattr(verification_cog, cmd)]
    print(f"Test 4b: Commands found: {found_commands}")
    
except Exception as e:
    print(f"Test 4: Member inspection - FAILED: {e}")

# Test 5: Check for obvious runtime errors (without Discord bot instance)
try:
    # Just validate the class structure
    if hasattr(verification_cog, 'VerificationCog'):
        print("Test 5a: VerificationCog class exists - PASSED")
    
    if hasattr(verification_cog, 'VerificationAttempt'):
        print("Test 5b: VerificationAttempt class exists - PASSED")
    
    if hasattr(verification_cog, 'VerificationPanelView'):
        print("Test 5c: VerificationPanelView class exists - PASSED")
        
    if hasattr(verification_cog, 'SUSRecoveryPanelView'):
        print("Test 5d: SUSRecoveryPanelView class exists - PASSED")
        
    if hasattr(verification_cog, 'ChallengeButton'):
        print("Test 5e: ChallengeButton class exists - PASSED")
    
except Exception as e:
    print(f"Test 5: Class structure check - FAILED: {e}")

print("\n=== All tests completed ===")
