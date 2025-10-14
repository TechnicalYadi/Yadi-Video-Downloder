$(document).ready(function () {

  // Step 1: Get video info
  $("#urlForm").submit(function (e) {
    e.preventDefault();
    const url = $("#url").val();
    $("#status").text("Fetching video info...");

    $.post("/info", { url: url }, function (data) {
      if (data.error) {
        $("#status").text("❌ " + data.error);
        return;
      }
      $("#video-info").show();
      $("#video-title").text("🎬 " + data.title);
      $("#video-duration").text("🕒 Duration: " + data.duration + " min");
      $("#download-url").val(url);

      $("#quality").empty();
      data.formats.forEach(f => {
        $("#quality").append(`<option value="${f.id}">${f.res} (${f.size}, ${f.ext})</option>`);
      });
      $("#status").text("Select quality and click Download 👇");
    });
  });

  // Step 2: Start download
  $("#downloadForm").submit(function (e) {
    e.preventDefault();
    $.post("/download", $(this).serialize(), function () {
      $("#status").text("🔄 Download started...");
      const interval = setInterval(() => {
        $.getJSON("/progress", function (data) {
          $("#bar").css("width", data.progress);
          $("#status").html(
            `📦 ${data.progress} | 💨 ${data.speed} | ⏳ Remaining: ${data.eta}<br>
             🎥 ${data.title || ""} | 💾 ${data.filesize || ""} | 🕒 ${data.duration || ""}`
          );
          if (data.status === "done" || data.status.startsWith("error")) {
            clearInterval(interval);
            $("#status").html(
              data.status.startsWith("error")
                ? `❌ Error: ${data.status}`
                : "✅ Download complete (Audio + Video merged)!"
            );
          }
        });
      }, 1000);
    });
  });
});
