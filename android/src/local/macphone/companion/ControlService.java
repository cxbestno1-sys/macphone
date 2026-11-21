package local.macphone.companion;
import android.accessibilityservice.*;import android.view.accessibility.*;import android.os.*;import android.app.KeyguardManager;import android.content.Context;import android.graphics.Path;import android.graphics.Rect;import android.util.DisplayMetrics;import android.view.WindowManager;import org.json.*;import java.net.*;import java.io.*;import java.util.concurrent.*;
public class ControlService extends AccessibilityService {
 private PowerManager.WakeLock cpuLock;
 public static volatile ControlService instance;private ServerSocket server;private final Handler main=new Handler(Looper.getMainLooper());private final ExecutorService workers=Executors.newFixedThreadPool(2);private final ExecutorService reader=Executors.newSingleThreadExecutor();
 @Override public void onAccessibilityEvent(AccessibilityEvent e){}@Override public void onInterrupt(){}
 @Override public void onServiceConnected(){instance=this;
 android.app.NotificationManager nm=(android.app.NotificationManager)getSystemService(NOTIFICATION_SERVICE);nm.createNotificationChannel(new android.app.NotificationChannel("macphone_control","MacPhone 手机控制",android.app.NotificationManager.IMPORTANCE_LOW));
 android.app.PendingIntent open=android.app.PendingIntent.getActivity(this,0,new android.content.Intent(this,MainActivity.class),android.app.PendingIntent.FLAG_IMMUTABLE|android.app.PendingIntent.FLAG_UPDATE_CURRENT);
 startForeground(1001,new android.app.Notification.Builder(this,"macphone_control").setContentTitle("MacPhone 控制服务运行中").setContentText("保持电脑控制连接，打开助手可关闭控制").setSmallIcon(android.R.drawable.ic_menu_view).setContentIntent(open).setOngoing(true).build());
 cpuLock=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"MacPhone:control");cpuLock.acquire();
new Thread(()->{try{server=new ServerSocket(18765,4,InetAddress.getByName("127.0.0.1"));while(!server.isClosed()){Socket s=server.accept();workers.submit(()->handle(s));}}catch(Exception e){android.util.Log.e("MacPhone","Control server",e);}},"MacPhone-server").start();}
 @Override public void onDestroy(){instance=null;if(cpuLock!=null&&cpuLock.isHeld())cpuLock.release();stopForeground(true);try{if(server!=null)server.close();}catch(Exception ignored){}workers.shutdownNow();reader.shutdownNow();super.onDestroy();}
 void handle(Socket socket){try{Socket s=socket;s.setSoTimeout(5000);BufferedReader in=new BufferedReader(new InputStreamReader(s.getInputStream(),"UTF-8"));String line=in.readLine();if(line==null||line.length()>20000)throw new Exception("Invalid request");JSONObject q=new JSONObject(line),r;
 if(!MainActivity.token(this).equals(q.optString("token")))throw new Exception("配对密钥不正确");
 if(q.optString("type").equals("status")){r=new JSONObject().put("ok",true).put("enabled",MainActivity.prefs(this).getBoolean("enabled",false)).put("locked",locked()).put("service",true);}else{
 if(!MainActivity.prefs(this).getBoolean("enabled",false))throw new Exception("请在手机助手中允许控制");if(q.optString("type").equals("wake")){wake();r=new JSONObject().put("ok",true).put("awake",true);respond(s,r);return;}if(locked())throw new Exception("手机已锁屏，请手动解锁");if(q.optString("type").equals("ui")){Future<JSONObject> f=reader.submit(()->{JSONArray nodes=new JSONArray();walk(getRootInActiveWindow(),nodes,0,SystemClock.uptimeMillis()+900,new int[]{0});return new JSONObject().put("ok",true).put("nodes",nodes);});try{r=f.get(1200,TimeUnit.MILLISECONDS);}catch(Exception e){f.cancel(true);r=new JSONObject().put("ok",true).put("nodes",new JSONArray()).put("partial",true);}}else r=execute(q);}
 respond(s,r);
 }catch(Exception e){try{respond(socket,new JSONObject().put("ok",false).put("error",(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage())));}catch(Exception ignored){}}finally{try{socket.close();}catch(Exception ignored){}}}
 void respond(Socket s,JSONObject r)throws Exception{s.getOutputStream().write((r.toString()+"\n").getBytes("UTF-8"));s.getOutputStream().flush();}
 void wake()throws Exception{
 KeyguardManager keyguard=(KeyguardManager)getSystemService(KEYGUARD_SERVICE);
 PowerManager pm=(PowerManager)getSystemService(POWER_SERVICE);
 if(!pm.isInteractive()){PowerManager.WakeLock lock=pm.newWakeLock(PowerManager.SCREEN_BRIGHT_WAKE_LOCK|PowerManager.ACQUIRE_CAUSES_WAKEUP,"MacPhone:wake");lock.acquire(10000);}
 if(keyguard.isKeyguardLocked()){
 if(keyguard.isKeyguardSecure())throw new Exception("屏幕已唤醒，请手动验证锁屏密码");
 android.content.Intent intent=new android.content.Intent(this,WakeActivity.class);intent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);startActivity(intent);
 }
 }
 boolean locked(){return ((KeyguardManager)getSystemService(Context.KEYGUARD_SERVICE)).isKeyguardLocked();}
 float coord(JSONObject q,String k,int size)throws Exception{double v=q.getDouble(k);if(Double.isNaN(v)||v<0||v>1)throw new Exception("坐标必须在0到1之间");return (float)(v*(size-1));}
 JSONObject execute(JSONObject q)throws Exception{CompletableFuture<JSONObject> result=new CompletableFuture<>();main.post(()->{if(result.isDone())return;try{
 String t=q.getString("type");boolean ok=false;

 if(t.equals("tap")||t.equals("swipe")){DisplayMetrics m=new DisplayMetrics();((WindowManager)getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRealMetrics(m);Path path=new Path();path.moveTo(coord(q,"x",m.widthPixels),coord(q,"y",m.heightPixels));long duration=80;if(t.equals("swipe")){path.lineTo(coord(q,"x2",m.widthPixels),coord(q,"y2",m.heightPixels));duration=(long)(Math.max(.15,Math.min(2,q.optDouble("duration",.5)))*1000);}
 GestureDescription g=new GestureDescription.Builder().addStroke(new GestureDescription.StrokeDescription(path,0,duration)).build();boolean accepted=dispatchGesture(g,new GestureResultCallback(){@Override public void onCompleted(GestureDescription g){finish(result,true,null);}@Override public void onCancelled(GestureDescription g){finish(result,false,"手势被系统取消");}},main);if(!accepted)finish(result,false,"系统未接受手势");return;
 }else if(t.equals("key")){String k=q.getString("key");if(k.equals("sleep"))ok=performGlobalAction(GLOBAL_ACTION_LOCK_SCREEN);else if(k.equals("home"))ok=performGlobalAction(GLOBAL_ACTION_HOME);else if(k.equals("back"))ok=performGlobalAction(GLOBAL_ACTION_BACK);else if(k.equals("recents"))ok=performGlobalAction(GLOBAL_ACTION_RECENTS);else throw new Exception("无障碍模式支持 home/back/recents 按键");
 }else if(t.equals("text")){AccessibilityNodeInfo root=getRootInActiveWindow();AccessibilityNodeInfo focus=root==null?null:root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT);if(focus==null||!focus.isEditable())throw new Exception("请先点击可编辑输入框");if(focus.isPassword())throw new Exception("密码框请在手机上手动填写");String text=q.getString("text");if(text.length()>10000)throw new Exception("文本过长");Bundle b=new Bundle();b.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,text);ok=focus.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,b);
 }else throw new Exception("未知动作");finish(result,ok,ok?null:"控件拒绝执行此动作");
 }catch(Exception e){finish(result,false,e.getMessage());}});try{return result.get(5,TimeUnit.SECONDS);}catch(TimeoutException e){result.cancel(false);throw new Exception("手机执行超时，请检查无障碍服务");}}
 void walk(AccessibilityNodeInfo node,JSONArray out,int depth,long deadline,int[] visited)throws Exception{
 if(node==null||depth>20||out.length()>=80||visited[0]++>200||Thread.currentThread().isInterrupted()||SystemClock.uptimeMillis()>deadline)return;
 if(node.isVisibleToUser()&&!node.isPassword()){
 String text=node.getText()==null?"":node.getText().toString();String label=node.getContentDescription()==null?"":node.getContentDescription().toString();
 if(node.isClickable()||node.isEditable()||!text.isEmpty()||!label.isEmpty()){
 Rect r=new Rect();node.getBoundsInScreen(r);DisplayMetrics m=new DisplayMetrics();((WindowManager)getSystemService(WINDOW_SERVICE)).getDefaultDisplay().getRealMetrics(m);
 JSONObject o=new JSONObject().put("text",text.substring(0,Math.min(120,text.length()))).put("label",label.substring(0,Math.min(120,label.length()))).put("clickable",node.isClickable()).put("editable",node.isEditable()).put("x",(double)r.centerX()/m.widthPixels).put("y",(double)r.centerY()/m.heightPixels);out.put(o);
 }}
 for(int i=0;i<node.getChildCount()&&out.length()<80&&SystemClock.uptimeMillis()<deadline&&!Thread.currentThread().isInterrupted();i++)walk(node.getChild(i),out,depth+1,deadline,visited);
 }
 static void finish(CompletableFuture<JSONObject> f,boolean ok,String error){try{JSONObject o=new JSONObject().put("ok",ok);if(error!=null)o.put("error",error);f.complete(o);}catch(Exception e){f.completeExceptionally(e);}}
}
