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