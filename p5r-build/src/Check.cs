using System;
using System.IO;
using System.Reflection;
using System.Runtime.Loader;
using System.Collections;
public class Check {
 public static void Main(string[] args) {
  AssemblyLoadContext.Default.Resolving += (ctx,n) => {
   string p=Path.Combine(Path.GetFullPath(args[2]),n.Name+".dll");
   return File.Exists(p)?ctx.LoadFromAssemblyPath(p):null;
  };
  var asm=AssemblyLoadContext.Default.LoadFromAssemblyPath(Path.GetFullPath(args[0]));
  var types=asm.GetTypes();
  var t=asm.GetType("SkillRename");var mod=Activator.CreateInstance(t);
  string path=Path.GetFullPath(args[1]);
  var flags=BindingFlags.Instance|BindingFlags.NonPublic;
  t.GetField("path",flags).SetValue(mod,path);t.GetField("id",flags).SetValue(mod,"p5rpc.skillrename");
  var method=t.GetMethod("Bind");var ct=method.GetParameters()[0].ParameterType;
  var context=Activator.CreateInstance(ct);var prop=ct.GetProperty("RelativePathToFileMap");
  var map=(IDictionary)Activator.CreateInstance(prop.PropertyType);prop.SetValue(context,map);
  method.Invoke(mod,new[]{context});method.Invoke(mod,new[]{context});
  var list=(IList)map[@"R2\BATTLE\TABLE\NAME.TBL"];
  if(list.Count!=1 || (string)list[0].GetType().GetField("FullPath").GetValue(list[0])!=path)throw new Exception("Wrong binding");
  Console.WriteLine("PASS: runtime="+Environment.Version+"; GetTypes, instantiate, repeated binding verified.");
 }
}
