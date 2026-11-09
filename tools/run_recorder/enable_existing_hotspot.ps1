$ErrorActionPreference='Stop'
$evidenceRoot=Join-Path (Resolve-Path "$PSScriptRoot/../..").Path ('results/preflights/HBPSN03_HOTSPOT_'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ'))
New-Item -ItemType Directory -Path $evidenceRoot | Out-Null
function Save-Evidence($name,$value) { $value | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $evidenceRoot $name) -Encoding UTF8 }
function Get-PasswordHash($value) { $hasher=[System.Security.Cryptography.SHA256]::Create(); try { ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($value)))).Replace('-','').ToLowerInvariant() } finally { $hasher.Dispose() } }
try {
 Add-Type -AssemblyName System.Runtime.WindowsRuntime
 $profile=[Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime]::GetInternetConnectionProfile()
 if ($profile.ProfileName -ne 'Ethernet') { throw 'Internet sharing source is no longer the previously observed Ethernet profile. No activation attempted.' }
 $manager=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]::CreateFromConnectionProfile($profile)
 $config=$manager.GetCurrentAccessPointConfiguration()
 $before=@{utc=[DateTime]::UtcNow.ToString('o');sharing_profile=$profile.ProfileName;state=$manager.TetheringOperationalState.ToString();ssid=$config.Ssid;band=$config.Band.ToString();password_sha256=(Get-PasswordHash $config.Passphrase);client_count=$manager.ClientCount;method='Existing saved AP configuration; StartTetheringAsync only, no ConfigureAccessPointAsync or setters'}
 Save-Evidence 'before.json' $before
 if ($before.band -ne 'TwoPointFourGigahertz') { throw ('Saved band is '+$before.band+'; no activation attempted because 2.4 GHz was required.') }
 if ($before.state -eq 'Off') {
  $operation=$manager.StartTetheringAsync()
  $method=[System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'} | Select-Object -First 1
  $resultType=[Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime]
  $task=$method.MakeGenericMethod($resultType).Invoke($null,@($operation))
  if (-not $task.Wait(30000)) { throw 'Hotspot activation outcome unknown after 30 seconds; no repeat requested.' }
  $result=$task.Result
  Save-Evidence 'activation_result.json' @{utc=[DateTime]::UtcNow.ToString('o');status=$result.Status.ToString();additional_error=$result.AdditionalErrorMessage;attempts=1}
  if ($result.Status.ToString() -ne 'Success') { throw ('Hotspot activation returned '+$result.Status.ToString()+' '+$result.AdditionalErrorMessage) }
 } elseif ($before.state -ne 'On') { throw ('Hotspot state '+$before.state+' is not stable. No repeat requested.') }
 $configAfter=$manager.GetCurrentAccessPointConfiguration()
 $after=@{utc=[DateTime]::UtcNow.ToString('o');sharing_profile=$profile.ProfileName;state=$manager.TetheringOperationalState.ToString();ssid=$configAfter.Ssid;band=$configAfter.Band.ToString();password_sha256=(Get-PasswordHash $configAfter.Passphrase);client_count=$manager.ClientCount;ipv4=@(Get-NetIPAddress -AddressFamily IPv4 | Select-Object IPAddress,InterfaceAlias,InterfaceIndex)}
 Save-Evidence 'after.json' $after
 if ($before.ssid -ne $after.ssid -or $before.password_sha256 -ne $after.password_sha256 -or $before.band -ne $after.band) { throw 'Saved AP configuration differs after activation; stop before board access.' }
 if ($after.state -ne 'On' -or -not @($after.ipv4 | Where-Object IPAddress -eq '192.168.137.1').Count) { throw 'Hotspot On and 192.168.137.1 both required; stop before board access.' }
 Save-Evidence 'PASS.json' @{utc=[DateTime]::UtcNow.ToString('o');state=$after.state;address='192.168.137.1';saved_configuration_preserved=$true;sharing_profile=$profile.ProfileName;band=$after.band;path=$evidenceRoot}
 Get-Content (Join-Path $evidenceRoot 'PASS.json')
} catch { Save-Evidence 'FAILURE.json' @{utc=[DateTime]::UtcNow.ToString('o');error=$_.Exception.Message;automatic_retry=$false}; throw }
