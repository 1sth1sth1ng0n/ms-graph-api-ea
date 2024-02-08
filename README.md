# ms-graph-api-extension-attribute 

Generates queries to the ms graph api in azure ad to obtain user group membership details.

Use case is for when your org has no ldap/ldaps service to utilize and jamf pro on-prem requires ldaps for scoping to azure ad groups. As we no longer bind to AD we cannot have the endpoints query AD directly. And we do not want to store api tokens etc on the endpoints, so the idea is to use a AWS function proxy api handler that responds to just basic requests when supplied a specific payload.

This AWS function is deployed using the serverless-framework and must include the corresponding IAM policy to give access to secrets manager where we store the azure api token and jamf api token. The policy is included separately but could be added to `serverless.yml`. You must also have created a app registration in azure to accomodate the api access.

You must also create a jamf extension attribute per Azure AD group. Then you can scope as needed. 

Example ea:

```
#!/bin/zsh

# use this if your org has office installed
#currentUser=$( scutil <<< "show State:/Users/ConsoleUser" | awk '/Name :/ && ! /loginwindow/ { print $3 }' )
#currentUserID=$(id -u "$currentUser")
#upn=$(launchctl asuser "$currentUserID" sudo -u "$currentUser" /usr/bin/defaults read com.microsoft.office OfficeActivationEmailAddress)
upn=$(/usr/libexec/PlistBuddy -c 'print :EMAIL' /Library/Managed\ Preferences/com.company.globalvariables.plist)
group='Azure AD Group Name'
serialNumber=$(system_profiler SPHardwareDataType | awk '/Serial/ {print $4}')
endpoint='https://ovqk3gyen4.execute-api.us-east-1.amazonaws.com/dev/email/validate'

result=$(curl -sL -X POST "${endpoint}" \
-H "Content-Type: text/plain" \
--data-raw "{
    \"email\":\"${upn}\",
    \"group\":\"${group}\",
    \"serialNumber\":\"${serialNumber}\"
}" | egrep -o '[0-9.]+')

echo "<result>$result</result>"
```

MS graph api token in app registration must be renewed yearly.
    
Endpoint payload request example:
    
```
{
	"email":"oliver.reardon@isthisthingon.online",
	"group":"Azure AD Group Name",
	"serialNumber":"C03DM8QBQ09N"
}
    
responce (member of group = true):
    
{
	"result": 1
}
```

