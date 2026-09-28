using System;
using System.IO;
using System.Collections.Generic;
using Reloaded.Mod.Interfaces;
using Reloaded.Mod.Interfaces.Internal;
using CriFs.V2.Hook.Interfaces;
public class SkillRename : IMod {
 private string path;
 private string id;
 public void StartEx(IModLoaderV1 loaderApi, IModConfigV1 config) {
  var loader=(IModLoader)loaderApi;
  id=((IModConfig)config).ModId;
  path=Path.Combine(loader.GetDirectoryForModId(id),"Data","NAME.TBL");
  if(!File.Exists(path)) throw new FileNotFoundException("SkillRename NAME.TBL missing",path);
  ICriFsRedirectorApi api;
  if(!loader.GetController<ICriFsRedirectorApi>().TryGetTarget(out api)) throw new InvalidOperationException("CRI API missing");
  api.AddBindCallback(Bind);
  Console.WriteLine("[SkillRename] Registered direct Simplified Chinese NAME.TBL binding.");
 }
 public void Bind(ICriFsRedirectorApi.BindContext context) {
  context.RelativePathToFileMap[@"R2\BATTLE\TABLE\NAME.TBL"]=new List<ICriFsRedirectorApi.BindFileInfo>{new ICriFsRedirectorApi.BindFileInfo{FullPath=path,LastWriteTime=File.GetLastWriteTimeUtc(path),ModId=id}};
  Console.WriteLine("[SkillRename] Bound Chinese NAME.TBL: Agi -> Fire I (Chinese). "+path);
 }
 public void Suspend(){} public void Resume(){} public void Unload(){}
 public bool CanUnload()=>false; public bool CanSuspend()=>false;
 public Action Disposing=>()=>{};
}
