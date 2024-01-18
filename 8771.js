<!-- start Simple Custom CSS and JS -->
<script type="text/javascript">
// Get the query parameters from the URL
    const urlParams = new URLSearchParams(window.location.search);
    const repoUrl = urlParams.get('datamodelRepoUrl');
    const email = urlParams.get('email');
	const testnumber = urlParams.get('testnumber');

    // Call the check_schema function and display the output
    function check_schema(repoUrl, email, testnumber) {
      var xmlhttp = new XMLHttpRequest();
      xmlhttp.open("GET", "https://smartdatamodels.org/extra/check_datamodel_test.php?datamodelRepoUrl=" + repoUrl + "&email=" + email + "&testnumber=" + testnumber, true);
      xmlhttp.send();

    xmlhttp.onload = function() {
    if (xmlhttp.status === 200) {
      document.getElementById("output").innerHTML = xmlhttp.responseText;
      if (xmlhttp.responseText.includes("#########")) {
        endInterval();
      }
    }
  };
}

function startInterval() {
  var repoUrl = document.getElementById("repoUrl").value;
  var email = document.getElementById("email").value;
  var testnumber = document.getElementById("testnumber").value;

  if (repoUrl && email && testnumber) {
        check_schema(repoUrl, email, testnumber);

        // Periodically update the PHP program every 2 seconds
        myTimer = setInterval(function() {
          check_schema(repoUrl, email, testnumber);
        }, 2000);
    }
}

function endInterval() {
  clearInterval(myTimer);
}</script>
<!-- end Simple Custom CSS and JS -->
