import sys
from collections import Counter

def find_frequent_users(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            users = [line.strip().split(':', 1)[0] for line in f if ':' in line]
    except FileNotFoundError:
        print(f"[!] File not found: {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error reading file: {e}")
        sys.exit(1)

    user_counts = Counter(users)

    print("Users occurring more than 3 times:\n")
    found = False
    for user, count in user_counts.items():
        if count > 3:
            print(f"{user}: {count} times")
            found = True

    if not found:
        print("No users occur more than 3 times.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <path_to_password_file>")
        sys.exit(1)

    filename = sys.argv[1]
    find_frequent_users(filename)
