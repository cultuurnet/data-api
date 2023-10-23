package be.publiq;
import com.google.api.client.http.GenericUrl;
import com.google.api.client.http.HttpRequest;
import com.google.api.client.http.HttpResponse;
import com.google.api.client.http.HttpTransport;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.auth.http.HttpCredentialsAdapter;
import com.google.auth.oauth2.GoogleCredentials;
import com.google.auth.oauth2.IdTokenCredentials;
import com.google.auth.oauth2.IdTokenProvider;
import java.io.IOException;

public class StatsectorSampleApp {

  // makeGetRequest makes a GET request to the specified Cloud Run or
  // Cloud Functions endpoint `serviceUrl` (must be a complete URL), by
  // authenticating with an ID token retrieved from Application Default
  // Credentials using the specified `audience`.
  //
  // Example `audience` value (Cloud Run): https://my-cloud-run-service.run.app/
  public static HttpResponse makeGetRequest(String serviceUrl, String audience) throws IOException {
    GoogleCredentials credentials = GoogleCredentials.getApplicationDefault();
    if (!(credentials instanceof IdTokenProvider)) {
      throw new IllegalArgumentException("Credentials are not an instance of IdTokenProvider.");
    }
    IdTokenCredentials tokenCredential =
        IdTokenCredentials.newBuilder()
            .setIdTokenProvider((IdTokenProvider) credentials)
            .setTargetAudience(audience)
            .build();

    GenericUrl genericUrl = new GenericUrl(serviceUrl);
    HttpCredentialsAdapter adapter = new HttpCredentialsAdapter(tokenCredential);
    HttpTransport transport = new NetHttpTransport();
    HttpRequest request = transport.createRequestFactory(adapter).buildGetRequest(genericUrl);
    return request.execute();
  }

  // main function
  public static void main(String [] args) {
    try {
      HttpResponse response = makeGetRequest("https://statsector-hwezb647ha-ew.a.run.app/get-statsector/?lat=50.870&lon=4.705", "https://statsector-hwezb647ha-ew.a.run.app");
      System.out.println(response.parseAsString());
    } catch (IOException e) {
      System.out.println("Error during authentication:");
      e.printStackTrace();
    }
  }
}