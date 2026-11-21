package local.macphone.companion;
import android.app.Activity;import android.os.Bundle;import android.content.Intent;import android.provider.Settings;import android.widget.*;import android.graphics.Color;import android.content.SharedPreferences;import java.security.SecureRandom;
public class MainActivity extends Activity {
 public static SharedPreferences prefs(android.content.Context c){return c.getSharedPreferences("control",0);}
 public static String token(android.content.Context c){SharedPreferences p=prefs(c);String t=p.getString("token",null);if(t==null){byte[] b=new byte[16];new SecureRandom().nextBytes(b);StringBuilder s=new StringBuilder();for(byte x:b)s.append(String.format("%02x",x));t=s.toString();p.edit().putString("token",t).apply();}return t;}
 @Override public void onCreate(Bundle b){super.onCreate(b);show();}
 @Override public void onResume(){super.onResume();show();}
 void show(){LinearLayout l=new LinearLayout(this);l.setOrientation(1);l.setPadding(48,60,48,32);l.setBackgroundColor(Color.rgb(242,246,252));ScrollView scroll=new ScrollView(this);scroll.addView(l);setContentView(scroll);
 Button guide=new Button(this);guide.setText("首次连接设置向导");guide.setOnClickListener(v->startActivity(new Intent(this,SetupActivity.class)));l.addView(guide);
 TextView paired=new TextView(this);paired.setText("已扫码配对电脑："+prefs(this).getString("pairedMac","尚未配对")+"\n使用系统扫一扫扫描MacPhone设置页二维码");l.addView(paired);
 TextView title=new TextView(this);title.setText("MacPhone 助手");title.setTextSize(28);l.addView(title);
 TextView text=new TextView(this);text.setText("\n让 Mac 控制你的手机\n\n1. 开启下方无障碍服务\n2. 打开允许控制开关\n3. 将配对密钥填入 MacPhone\n\n控制服务只监听手机本机，通过已授权的 ADB USB / Wi-Fi 通道连接。锁屏后不接受操作。\n");text.setTextSize(16);l.addView(text);
 TextView status=new TextView(this);status.setText(ControlService.instance==null?"无障碍服务：未开启":"无障碍服务：已开启");l.addView(status);
 Button open=new Button(this);open.setText("打开无障碍设置");open.setOnClickListener(v->startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));l.addView(open);
 Switch enabled=new Switch(this);enabled.setText("允许已配对的 Mac 控制");enabled.setChecked(prefs(this).getBoolean("enabled",false));enabled.setOnCheckedChangeListener((v,on)->prefs(this).edit().putBoolean("enabled",on).apply());l.addView(enabled);
 TextView label=new TextView(this);label.setText("\n配对密钥（仅提供给你的 Mac）：\n"+token(this));label.setTextIsSelectable(true);label.setTextSize(17);l.addView(label);
 Button reset=new Button(this);reset.setText("撤销配对并生成新密钥");reset.setOnClickListener(v->{prefs(this).edit().remove("token").putBoolean("enabled",false).commit();show();});l.addView(reset);
 EditText test=new EditText(this);test.setHint("输入测试框：可从 Mac 输入中文");l.addView(test);
 TextView note=new TextView(this);note.setText("\n若系统阻止开启，请在应用信息右上角检查“允许受限设置”。请手动阅读并确认系统授权提示。");l.addView(note);
 }
}
