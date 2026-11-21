package local.macphone.companion;
import android.app.Activity;import android.os.Bundle;import android.content.Intent;import android.provider.Settings;import android.widget.*;
public class SetupActivity extends Activity {
 LinearLayout content;
 @Override public void onCreate(Bundle b){super.onCreate(b);ScrollView scroll=new ScrollView(this);content=new LinearLayout(this);content.setOrientation(1);content.setPadding(40,60,40,40);scroll.addView(content);setContentView(scroll);
 text("MacPhone 首次连接向导",26);
 text("1 · 电脑和手机准备\nMac端把MacPhone放入应用程序，手机安装MacPhone助手。优先用能传数据的USB线首次连接。",17);
 text("2 · 开启开发者选项\n在关于手机中，连续点击系统版本/版本号，直到提示已进入开发者模式。不同品牌位置不同。",17);button("打开关于手机",Settings.ACTION_DEVICE_INFO_SETTINGS);
 text("3 · 开启USB调试\n进入开发者选项，开启USB调试。连接Mac后，在手机弹窗中允许这台电脑。普通App无法代替你打开这个开关。",17);button("打开开发者选项",Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS);
 text("4 · 开启辅助控制\n在无障碍的已安装服务中启用MacPhone手机控制。若提示受限设置，先到助手应用信息中检查允许受限设置，再返回授权。",17);button("打开无障碍设置",Settings.ACTION_ACCESSIBILITY_SETTINGS);
 text("5 · 允许控制并配对\n回到助手首页，打开允许已配对的Mac控制，将32位密钥填入MacPhone设置。不要把密钥发给其他人。",17);
 text("6 · 切换Wi-Fi（可选）\n保持USB连接，在Mac向导点通过USB配置Wi-Fi，验证成功后再拔线。手机重启后可能需要重新启用。另一方式是开发者选项中的无线调试配对。",17);
 text("扫码配对说明\n扫码目前仅记录电脑身份，不能替代ADB连接。控制和文件传输仍需要完成上面步骤。",17);
 Button done=new Button(this);done.setText("返回助手首页");done.setOnClickListener(v->finish());content.addView(done);
 }
 void text(String text,int size){TextView view=new TextView(this);view.setText(text+"\n");view.setTextSize(size);view.setPadding(0,14,0,14);content.addView(view);}
 void button(String title,String action){Button b=new Button(this);b.setText(title);b.setOnClickListener(v->{try{startActivity(new Intent(action));}catch(Exception e){Toast.makeText(this,"此手机不支持直接跳转，请手动打开设置",Toast.LENGTH_LONG).show();}});content.addView(b);}
}
