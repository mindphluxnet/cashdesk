var running = false;
var kassiervorgang = false;
var abrechnung = false;
var bonsumme = 0;
var wechselgeld = 0;
var positionen = {};

loadState();
restoreState();

function scrollDown() {
  $("#bonrolle").scrollTop($("#bonrolle")[0].scrollHeight);
}

function addLine(line) {
  $('#bonrolle').append('<p>' + line + '</p>');
}

function addBlankLine() {
  $('#bonrolle').append('<p>&nbsp;</p>');
}

function addSpacer() {
    star = "*";
    spacer = star.repeat(40);
    addLine(spacer);
}

function addDivisor() {
  dash = "-";
  div = dash.repeat(40);
  addLine(div);
}

function addTotalSumDivisor() {
  dash = "=";
  div = dash.repeat(40);
  addLine(div);
}

function addLineCentered(line) {

  var l = line.length;
  var leer = "&nbsp;";
  var pad = (40 - l) / 2;

  if(pad % 2 == 0) {
    out = leer.repeat(pad) + line + leer.repeat(pad);
  }
  else {
    out = leer.repeat(Math.round(pad)) + line + leer.repeat(Math.round(pad));
  }

  addLine(out);

}

function addLineWaehrung() {

  var leer = "&nbsp;";
  var line = leer.repeat(37) + "EUR";
  addLine(line);

}

function zeroPad(num) {

  if(num >= 0 && num < 10) {
    num = '0' + num;
  }
  return num;
}

function updateBonSumme(data) {

  var anzahl = $('#anzahl').val();
  var summe = anzahl * data.vkpreis;
  bonsumme += summe;
  $('#bonsumme').html(bonsumme.toFixed(2).toString());

}

function bonHeader(kassiervorgang = false) {

  addLineCentered(stammdaten.firmenname);
  addBlankLine();
  addLineCentered(stammdaten.inhaber);
  addLineCentered(stammdaten.strasse + ' ' + stammdaten.hausnummer);
  addLineCentered(stammdaten.plz.toString() + ' ' + stammdaten.ort);
  addBlankLine();

  if(kassiervorgang) {
    addLineWaehrung();
  }

}

function buildItemLine(data) {

  leer = "&nbsp;";
  artbez = data.artikelbezeichnung;
  artbez = artbez.substring(0, 16).toUpperCase();
  preis = data.vkpreis.toString();

  if(anzahl >= 999) {
    anzahl = 999;
  }

  if(anzahl <= 0) {
    anzahl = 1;
  }

  if(anzahl > 1) {
    gesamtpreis = anzahl * preis;
    gp = gesamtpreis.toFixed(2).toString();
  }

  if(anzahl > 1) {
    pad = 40 - artbez.length - gp.length;
    line = artbez + leer.repeat(pad) + gp;
    addLine(line);

    anz = anzahl.toString();
    line = leer.repeat(3 - anz.length) + anz + leer.repeat(1) + "x" + leer.repeat(16 - preis.length) + preis;
    addLine(line);

  }
  else {
      pad = 40 - artbez.length - preis.length;
      line = artbez + leer.repeat(pad) + preis;
      addLine(line);
  }


}

function printReceipt() {

}

function saveState() {

  $.remember({ name: 'kassiervorgang', value: kassiervorgang});
  $.remember({ name: 'running', value: running});
  $.remember({ name: 'bonsumme', value: bonsumme});
  $.remember({ name: 'wechselgeld', value: wechselgeld});
  $.remember({ name: 'abrechnung', value: abrechnung});
  $.remember({ name: 'positionen', value: positionen});

}

function loadState() {

    kassiervorgang = $.remember( { name: 'kassiervorgang' } );
    running = $.remember( { name: 'running' } );
    bonsumme = parseFloat($.remember( { name: 'bonsumme' } ));
    wechselgeld = parseFloat($.remember( { name: 'wechselgeld' } ));
    abrechnung = $.remember( { name: 'abrechnung' } );
    positionen = $.remember( { name: 'positionen' } );

    if(isNaN(bonsumme)) bonsumme = 0;
    if(isNaN(wechselgeld)) wechselgeld = 0;

}

function restoreState() {

  if(kassiervorgang && running && wechselgeld > 0) {

    $('#kasse-wechselgeld').attr('disabled', 'disabled');
    $('#kasse-starten').attr('disabled', 'disabled');
    $('#kasse-abrechnen').removeAttr('disabled');
    $('#anzahl-panel').removeClass('hidden');
    $('#ean-panel').removeClass('hidden');
    $('#bonsumme-panel').removeClass('hidden');
    $('#bonsumme').html(bonsumme.toFixed(2));
    $('#ean').focus();

  }

  if(!running && !kassiervorgang && wechselgeld == 0) {

    $('#kasse-wechselgeld').removeAttr('disabled')
    $('#kasse-starten').attr('disabled', 'disabled');
    $('#kasse-abrechnen').attr('disabled', 'disabled');
    $('#anzahl-panel').addClass('hidden');
    $('#ean-panel').addClass('hidden');
    $('#bonsumme-panel').addClass('hidden');

  }


}

function addPosition(data) {

  

}

// ============================================================ kasse starten ================================================

$('#kasse-starten').on('click', function() {

  if(running) return;

  $('#kasse-wechselgeld').attr('disabled', 'disabled');
  $('#kasse-starten').attr('disabled', 'disabled');
  $('#kasse-abrechnen').removeAttr('disabled');
  $('#anzahl-panel').removeClass('hidden');
  $('#ean-panel').removeClass('hidden');
  $('#bonsumme-panel').removeClass('hidden');
  $('#bonrolle').html('');
  $('#ean').focus();

  running = true;
  saveState();

});

// ============================================================ wechselgeld ===================================================

function wechselgeldBuchen() {

  wechselgeld = $('#wechselgeld').val();

  var now = new Date();

  $.ajax({
    url: '/ajax/kasse/buchung',
    method: 'POST',
    data: { 'event': 'wechselgeld', 'betrag': wechselgeld, 'artikel_id': 0, 'datum': now, 'anzahl': 0 },
    success: function(result) {
      result = JSON.parse(result);
    }
  });

}

$('#kasse-wechselgeld').on('click', function() {

  $('#modal-wechselgeld').modal();

});

$('.btn-wechselgeld').on('click', function() {

  wg = $(this).data('wg');
  $('#wechselgeld').val(wg);

});

$('#wechselgeld-ok').on('click', function() {
  wechselgeld = $('#wechselgeld').val();
})

$('#wechselgeld').on('keydown', function(e) {

  var keycode = e.keyCode || e.which;

  if(keycode == 13) {
    $('#wechselgeld-ok').click();

  }

});

$('#modal-wechselgeld').on('shown.bs.modal', function() {
  $('#wechselgeld').focus();
});

$('#modal-wechselgeld').on('hidden.bs.modal', function() {

  if(wechselgeld > 0) {

    var now = new Date();

    bonHeader();
    addDivisor();
    addBlankLine();
    addLineCentered("Kassenstartbeleg");
    addBlankLine();
    addLineCentered('WECHSELGELD: EUR ' + wg.toFixed(2).toString());
    addBlankLine();
    addLineCentered('DATUM: ' + zeroPad(now.getDate()) + '.' + zeroPad(now.getMonth()) + '.' + now.getFullYear() + ' UHRZEIT: ' + zeroPad(now.getHours()) + ':' + zeroPad(now.getMinutes()));
    addBlankLine();
    addDivisor();

    wechselgeldBuchen();

    printReceipt();
    $('#kasse-wechselgeld').attr('disabled', 'disabled');
    $('#kasse-starten').removeAttr('disabled');

    saveState();

  }

});

// =========================================================== kassiervorgang ================================================================

$('#ean').on('keydown', function(e) {

  var keycode = e.keyCode || e.which;

  if(keycode == 13) {

    var ean = $(this).val();
    var anzahl = $('#anzahl').val();

    $.ajax({
      url: '/ajax/artikel/byean',
      method: 'POST',
      data: { 'ean': ean },
      success: function(result) {
        if(result != 'null') {

          data = JSON.parse(result);

          if(!kassiervorgang) {
            bonHeader(true);
            kassiervorgang = true;
          }

          updateBonSumme(data);
          buildItemLine(data);
          addPosition(data);

          $('.btn-anzahl').removeClass('btn-success');
          $('#mehrals10').removeClass('btn-success');
          $('#anzahl').val('');
          scrollDown();
          $('#ean').val('');
          $('#ean').focus();
          saveState();
        }
        else {
          $('#modal-artikel-nicht-gefunden').modal();
        }

      }
    });
  }

});

$('.btn-anzahl').on('click', function() {

  $('.btn-anzahl').removeClass('btn-success');
  anzahl = $(this).data('anzahl');
  $('#anzahl').val(anzahl);
  $(this).addClass('btn-success');
  $('#ean').focus();

});

$('#mehrals10').on('click', function() {
  $('#anzahl-eingeben').modal();
});

$('#anzahl-eingeben').on('shown.bs.modal', function() {
  $('#mehr-anzahl').val('');
  $('#mehr-anzahl').focus();
});

$('#anzahl-eingeben').on('hidden.bs.modal', function() {
  $('#ean').focus();
});

$('#modal-artikel-nicht-gefunden').on('hidden.bs.modal', function() {
  $('#ean').val('');
  $('#ean').focus();
});

$('#mehr-anzahl-ok').on('click', function() {
  anzahl = $('#mehr-anzahl').val();
  $('#anzahl').val(anzahl);
  if(anzahl > 10)
  {
    $('.btn-anzahl').removeClass('btn-success');
    $('#mehrals10').addClass('btn-success');
  }
  else {
    $('#mehrals10').removeClass('btn-success');
    $('.btn-anzahl').removeClass('btn-success');
    $(".btn-anzahl[data-anzahl='" + anzahl + "']").addClass('btn-success');
  }
});

$('#mehr-anzahl').on('keydown', function(e) {
  var keycode = e.keyCode || e.which;

  if(keycode == 13) {
      $('#mehr-anzahl-ok').click();
  }
});

$('#artikelselect-ok').on('click', function() {

  artikel_id = $('#artikelselect').val();
  $.ajax({
    url: '/ajax/artikel/byid',
    method: 'POST',
    data: { 'id': artikel_id },
    success: function(result) {
      data = JSON.parse(result);

      if(!kassiervorgang) {
        bonHeader();
        kassiervorgang = true;
      }

      updateBonSumme(data);
      buildItemLine(data);
      addPosition(data);

      $('.btn-anzahl').removeClass('btn-success');
      $('#mehrals10').removeClass('btn-success');
      $('#anzahl').val('');
      scrollDown();
      $('#ean').val('');
      $('#ean').focus();
      saveState();
    }
  });

});
