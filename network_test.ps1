
$link_speed = (Get-NetAdapter | Where-Object Name -eq Ethernet | Select -expand LinkSpeed).toString()
if (!$link_speed.Contains("Gbps")){
    Write-Output("Re-insert Ethernet Cable")
	Read-Host -Prompt "Press Enter to exit"
}
