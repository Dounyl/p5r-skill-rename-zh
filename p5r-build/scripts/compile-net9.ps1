$ErrorActionPreference = 'Stop'
$buildRoot = Split-Path $PSScriptRoot -Parent
$outDir = Join-Path $buildRoot 'temp/loader'
New-Item -ItemType Directory -Force $outDir | Out-Null
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.dll')
Add-Type -Path (Join-Path $PSHOME 'Microsoft.CodeAnalysis.CSharp.dll')
$refPaths=@(Get-ChildItem (Join-Path $buildRoot 'vendor/net9ref/ref/net9.0') -Filter '*.dll' | ForEach-Object FullName)+@((Join-Path $buildRoot 'vendor/Reloaded.Mod.Interfaces.dll'),(Join-Path $buildRoot 'vendor/CriFs.V2.Hook.Interfaces.dll'))
$refs=[System.Collections.Generic.List[Microsoft.CodeAnalysis.MetadataReference]]::new()
foreach($p in $refPaths){$refs.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile($p))}
$tree=[Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText([IO.File]::ReadAllText((Join-Path $buildRoot 'src/SkillRename.cs')))
$options=[Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions]::new([Microsoft.CodeAnalysis.OutputKind]::DynamicallyLinkedLibrary)
$comp=[Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create('SkillRename',[Microsoft.CodeAnalysis.SyntaxTree[]]@($tree),$refs,$options)
$stream=[IO.File]::Create((Join-Path $outDir 'SkillRename.dll'))
try{$result=$comp.Emit($stream);$result.Diagnostics | ForEach-Object ToString;if(-not $result.Success){throw 'Compile failed'}}finally{$stream.Dispose()}

Write-Output 'Compiled: temp/loader/SkillRename.dll'
