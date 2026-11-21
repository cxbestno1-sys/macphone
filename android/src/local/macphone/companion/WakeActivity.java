package local.macphone.companion;
import android.app.Activity;import android.app.KeyguardManager;import android.os.Bundle;import android.view.WindowManager;
public class WakeActivity extends Activity {
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);setShowWhenLocked(true);setTurnScreenOn(true);KeyguardManager k=(KeyguardManager)getSystemService(KEYGUARD_SERVICE);if(k.isKeyguardSecure()){finish();return;}k.requestDismissKeyguard(this,new KeyguardManager.KeyguardDismissCallback(){@Override public void onDismissSucceeded(){finish();}@Override public void onDismissCancelled(){finish();}@Override public void onDismissError(){finish();}});new android.os.Handler(getMainLooper()).postDelayed(()->finish(),2000);}
}
