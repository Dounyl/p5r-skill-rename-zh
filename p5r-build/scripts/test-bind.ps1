$ErrorActionPreference = 'Stop'
$buildRoot = Split-Path $PSScriptRoot -Parent
[System.Reflection.Assembly]::LoadFrom((Join-Path $buildRoot 'vendor/Reloaded.Mod.Interfaces.dll')) | Out-Null
[System.Reflection.Assembly]::LoadFrom((Join-Path $buildRoot 'vendor/CriFs.V2.Hook.Interfaces.dll')) | Out-Null
$asm=[System.Reflection.Assembly]::LoadFrom((Join-Path $buildRoot 'temp/loader/SkillRename.dll'))
$type=$asm.GetType('SkillRename')
$obj=[Activator]::CreateInstance($type)
$flags=[Reflection.BindingFlags]'Instance,NonPublic'
$path=(Resolve-Path (Join-Path $buildRoot '../p5rpc.skillrename/Data/NAME.TBL')).Path
$type.GetField('path',$flags).SetValue($obj,$path)
$type.GetField('id',$flags).SetValue($obj,'p5rpc.skillrename')
$context=New-Object 'CriFs.V2.Hook.Interfaces.ICriFsRedirectorApi+BindContext'
$context.RelativePathToFileMap=New-Object 'System.Collections.Generic.Dictionary[string,System.Collections.Generic.List[CriFs.V2.Hook.Interfaces.ICriFsRedirectorApi+BindFileInfo]]'
$obj.Bind($context)
$entry=$context.RelativePathToFileMap['R2\BATTLE\TABLE\NAME.TBL']
if($entry.Count -ne 1 -or $entry[0].FullPath -ne $path){throw 'Binding test failed'}
$obj.Bind($context)
if($context.RelativePathToFileMap.Count -ne 1){throw 'Repeated binding failed'}
'PASS: callback binds the exact Chinese table; repeated binding remains stable.'
