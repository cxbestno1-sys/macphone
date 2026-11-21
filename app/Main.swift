import AppKit
import WebKit
import CoreImage
class Delegate:NSObject,NSApplicationDelegate,WKNavigationDelegate,WKUIDelegate,WKScriptMessageHandler {
 var window:NSWindow!;var backend:Process!;var web:WKWebView!
 func applicationDidFinishLaunching(_ n:Notification){
  let resources=Bundle.main.resourceURL!
  backend=Process();backend.executableURL=resources.appendingPathComponent("python/bin/python3");backend.arguments=["-B",resources.appendingPathComponent("backend.py").path];var environment=ProcessInfo.processInfo.environment;environment["PYTHONHOME"]=resources.appendingPathComponent("python").path;environment["PYTHONDONTWRITEBYTECODE"]="1";backend.environment=environment
  let pipe=Pipe();backend.standardOutput=pipe
  do {try backend.run()}catch{NSAlert(error:error).runModal();NSApp.terminate(nil);return}
  window=NSWindow(contentRect:NSRect(x:0,y:0,width:1220,height:860),styleMask:[.titled,.closable,.miniaturizable,.resizable],backing:.buffered,defer:false)
  window.title="MacPhone";window.titlebarAppearsTransparent=true;window.backgroundColor=NSColor(calibratedRed:0.94,green:0.96,blue:0.99,alpha:1);window.minSize=NSSize(width:850,height:600);window.center()
  let config=WKWebViewConfiguration();config.userContentController.add(self,name:"files");config.userContentController.add(self,name:"qr");web=WKWebView(frame:.zero,configuration:config);web.navigationDelegate=self;web.uiDelegate=self;window.contentView=web;window.makeKeyAndOrderFront(nil);NSApp.activate(ignoringOtherApps:true)
  DispatchQueue.global().async {
   var data=Data()
   while let b=try? pipe.fileHandleForReading.read(upToCount:1), !b.isEmpty {if b[0]==10 {break};data.append(b)}
   if let obj=try? JSONSerialization.jsonObject(with:data) as? [String:Any],let port=obj["port"] as? Int {DispatchQueue.main.async{self.web.load(URLRequest(url:URL(string:"http://127.0.0.1:\(port)/")!))}}
  }
 }
 func webView(_ webView:WKWebView,decidePolicyFor action:WKNavigationAction,decisionHandler:@escaping(WKNavigationActionPolicy)->Void){decisionHandler(action.request.url?.host=="127.0.0.1" ? .allow:.cancel)}
 func webView(_ webView:WKWebView,runJavaScriptConfirmPanelWithMessage message:String,initiatedByFrame frame:WKFrameInfo,completionHandler:@escaping(Bool)->Void){let alert=NSAlert();alert.messageText=message;alert.addButton(withTitle:"确认");alert.addButton(withTitle:"取消");completionHandler(alert.runModal() == .alertFirstButtonReturn)}
 func userContentController(_ userContentController:WKUserContentController,didReceive message:WKScriptMessage){if message.name=="qr",message.frameInfo.request.url?.host=="127.0.0.1",let value=message.body as? String,value.hasPrefix("macphone://pair?"),let filter=CIFilter(name:"CIQRCodeGenerator"){filter.setValue(Data(value.utf8),forKey:"inputMessage");filter.setValue("M",forKey:"inputCorrectionLevel");if let output=filter.outputImage?.transformed(by:CGAffineTransform(scaleX:6,y:6)),let cg=CIContext().createCGImage(output,from:output.extent){let rep=NSBitmapImageRep(cgImage:cg);if let png=rep.representation(using:.png,properties:[:]),let data=try? JSONSerialization.data(withJSONObject:["image":"data:image/png;base64,"+png.base64EncodedString()]),let json=String(data:data,encoding:.utf8){web.evaluateJavaScript("showPairQR(\(json))",completionHandler:nil)}};return};guard message.name=="files",let mode=message.body as? String,["push","install"].contains(mode),message.frameInfo.request.url?.host=="127.0.0.1" else{return};let panel=NSOpenPanel();panel.canChooseDirectories=false;panel.allowsMultipleSelection=false;panel.beginSheetModal(for:window){response in guard response == .OK,let url=panel.url else{return};if let data=try? JSONSerialization.data(withJSONObject:["mode":mode,"path":url.path]),let json=String(data:data,encoding:.utf8){self.web.evaluateJavaScript("filePicked(\(json))",completionHandler:nil)}}}
 func applicationShouldTerminateAfterLastWindowClosed(_ sender:NSApplication)->Bool{true}
 func applicationWillTerminate(_ n:Notification){backend?.terminate()}
}
let app=NSApplication.shared;let delegate=Delegate();app.delegate=delegate;app.setActivationPolicy(.regular)
let menu=NSMenu();let item=NSMenuItem();menu.addItem(item);let submenu=NSMenu();submenu.addItem(withTitle:"退出 MacPhone",action:#selector(NSApplication.terminate(_:)),keyEquivalent:"q");item.submenu=submenu;app.mainMenu=menu;app.run()
