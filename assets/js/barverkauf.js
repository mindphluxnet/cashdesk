$(".button-anzahl[data-anzahl='1']").addClass('btn-success');
$('#anzahl').val(1);
$('#za-karte-info').hide();
if($('#bon_id').val() != '') {
  $('#barverkauf-starten').attr('disabled', 'disabled');
  $('#barverkauf-abbrechen').removeAttr('disabled');
  $('#barverkauf-abschliessen').removeAttr('disabled');
  $('.button-anzahl').removeAttr('disabled');
  $('#morethanthis').removeAttr('disabled');
  $('#ean').removeAttr('disabled');
  $('#ean').focus();
}

$('.button-anzahl').on('click', function() {

  anz = $(this).data('anzahl');

  $('.button-anzahl').removeClass('btn-success');
  $('#morethanthis').removeClass('btn-success');
  $('#morethanthis').text('> 10');
  $(this).addClass('btn-success');
  $('#anzahl').val(anz);
  $('#ean').focus();

});

$('#morethanthis').on('click', function() {
  $('#anzahl-eingeben').modal();
});

$('#anzahl-eingeben').on('shown.bs.modal', function() {
  $('#mehr-anzahl').focus();
});

$('#anzahl-eingeben').on('hidden.bs.modal', function() {
  $('#anzahl').val($('#mehr-anzahl').val());
  $('.button-anzahl').removeClass('btn-success');
  $('#morethanthis').addClass('btn-success');
  $('#morethanthis').text($('#anzahl').val());
  $('#ean').focus();
});

$('#anzahl-eingeben').on('keydown', function(e) {
  var keycode = e.keyCode || e.which;
  if(keycode == 13) {
      $('#mehr-anzahl-ok').click();
  }

});

$('#ean').on('keydown', function(e) {

  if($('#bon_id').val() == '') return;

  var keycode = e.keyCode || e.which;

  if(keycode == 13) {

      var ean = $('#ean').val();

      $.ajax({

        url: '/barverkauf/ajax/artikel',
        method: 'POST',
        data: { 'ean': ean },
        success: function(result) {

          result = JSON.parse(result);

          if(result.artikelbezeichnung == '') {
            $('#artikelnichtgefunden-modal').modal();
          }
          else {
            $('#pos_artikel_id').val(result.rowid);
            $('#pos_anzahl').val($('#anzahl').val());
            $('#position-neu-form').submit();
          }

        }


      });
  }

});

$('#barverkauf-starten').on('click', function() {

  $.ajax({
    url: '/barverkauf/starten',
    method: 'GET',
    success: function(result) {
      result = JSON.parse(result);
      if(result.bon_id != '') {
        $('#bon_id').val(result.bon_id);
        $('#barverkauf-starten').attr('disabled', 'disabled');
        $('#ean').removeAttr('disabled');
        $('#barverkauf-abbrechen').removeAttr('disabled');
        $('#barverkauf-abschliessen').removeAttr('disabled');
        $('.button-anzahl').removeAttr('disabled');
        $('#morethanthis').removeAttr('disabled');        
        $('#ean').focus();
      }

    }

  });

});

$('#barverkauf-abbrechen').on('click', function() {

  $('#barverkauf-abbrechen-modal').modal();

});

$('#barverkauf-abbrechen-ok').on('click', function() {

  bon_id = $('#bon_id').val();
  window.location = '/barverkauf/abbrechen/' + bon_id;

});

$('#barverkauf-abschliessen').on('click', function() {

  $('#gesamtbetrag-aus').text(gesamtsumme.toFixed(2));
  $('#za-bargeld-info-gesamtbetrag').val(gesamtsumme.toFixed(2));
  $('#barverkauf-abschliessen-modal').modal();

});

$('#barverkauf-abschliessen-modal').on('shown.bs.modal', function() {
  $('#za-bargeld-info-gegeben').focus();
});

$('.anzahl').on('change', function() {

    anz = $(this).val();
    id = $(this).data('id');

    $('#pa_pos_id').val(id);
    $('#pa_anzahl').val(anz);
    $('#pa_bon_id').val($('#bon_id').val());
    $('#position-aendern-form').submit();
  });


$('.deletebutton').on('click', function() {

  id = $(this).data('id');

  $.ajax({
    url: '/barverkauf/ajax/loeschen',
    method: 'POST',
    data: { 'id': id },
    success: function(result) {
      result = JSON.parse(result);
      $("tr[data-row='" + id + "']").remove();
      $('#ean').focus();

    }

  });

});

$('.cp').on('click', function() {

  $('.cp').removeClass('za-selected');
  $(this).addClass('za-selected');

});

$('#za-bar').on('click', function() {
  $('#za-karte-info').hide();
  $('#za-bargeld-info').show();
  $('#zahlungsart').val(1);
});

$('#za-ec').on('click', function() {
  $('#za-karte-info').show();
  $('#za-bargeld-info').hide();
  $('#zahlungsart').val(4);
});

$('#za-cc').on('click', function() {
  $('#za-karte-info').show();
  $('#za-bargeld-info').hide();
  $('#zahlungsart').val(5);
});

$('#za-bargeld-info-gegeben').on('keydown keyup blur', function(e) {

  var keycode = e.keyCode | e.which;

  if(keycode == 13) {
    event.preventDefault();
  }

  var gg = $(this).val();
  var gb = gesamtsumme;

  var wg = gb - gg;

  if(wg <= 0) {
    wg = -wg;
    $('#za-bargeld-info-wechselgeld').val(wg.toFixed(2));
  }
  else {
    $('#za-bargeld-info-wechselgeld').val('Gesamtbetrag nicht erreicht!');
  }

});
