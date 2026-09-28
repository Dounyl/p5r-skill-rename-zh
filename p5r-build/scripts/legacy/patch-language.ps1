Add-Type -Path (Join-Path $PSScriptRoot '../../vendor/cecil/lib/netstandard2.0/Mono.Cecil.dll')
$source = 'C:\Users\dan\Desktop\Reloaded-II\Mods\Reloaded.Universal.Localisation.Provider.Windows\Reloaded.Universal.Localisation.Provider.Windows.dll'
$outDir = Join-Path $PSScriptRoot '../../temp/P5R-zhCN-Fix'
New-Item -ItemType Directory -Force $outDir | Out-Null
$asm = [Mono.Cecil.AssemblyDefinition]::ReadAssembly($source)
$type = $asm.MainModule.Types | Where-Object Name -eq 'WindowsLanguage'
$method = $type.Methods | Where-Object Name -eq '.cctor'
$hit = @($method.Body.Instructions | Where-Object { $_.OpCode.Name -eq 'ldstr' -and $_.Operand -eq 'zh-Hans' })
if ($hit.Count -ne 1) { throw 'Unexpected original IL' }
$anchor = $hit[0].Next.Next.Next
$field = $hit[0].Next.Operand
$add = $hit[0].Next.Next.Operand
$il = $method.Body.GetILProcessor()
$il.InsertBefore($anchor, [Mono.Cecil.Cil.Instruction]::Create([Mono.Cecil.Cil.OpCodes]::Dup))
$il.InsertBefore($anchor, [Mono.Cecil.Cil.Instruction]::Create([Mono.Cecil.Cil.OpCodes]::Ldstr, 'zh-CN'))
$il.InsertBefore($anchor, [Mono.Cecil.Cil.Instruction]::Create([Mono.Cecil.Cil.OpCodes]::Ldsfld, [Mono.Cecil.FieldReference]$field))
$il.InsertBefore($anchor, [Mono.Cecil.Cil.Instruction]::Create([Mono.Cecil.Cil.OpCodes]::Callvirt, [Mono.Cecil.MethodReference]$add))
$asm.Write((Join-Path $outDir 'Reloaded.Universal.Localisation.Provider.Windows.dll'))
Copy-Item $source (Join-Path $outDir 'Reloaded.Universal.Localisation.Provider.Windows.dll.original') -Force
$asm.Dispose()
Write-Output 'Added zh-CN alias; all existing language mappings preserved.'
