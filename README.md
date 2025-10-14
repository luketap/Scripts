# new-target
This is a simple script to define variables for an active directory target such as a domain contoller. The purpase is to save time rather than typeing out every domain related detail. This can be especailly useful in CTFs.

## Usage
`source ./new-target`

### Examples:
```
bloodhound-ce-python -d "$domain" -u "$user" -p "$pass" -dc "$fqdn" -ns "$ip" -c All --dns-tcp --zip

certipy-ad find -vulnerable -dc-ip "$ip" -u "$user" -p "$pass"

impacket-GetADUsers -all "$domain"/"$user":"$pass" -dc-ip "$ip" > users.txt
```
