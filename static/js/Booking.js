$(document).ready(function () {
    $('input[type=radio][name=food]').change(function() {
        console.log("Selecting Food")
        req = $.ajax({
            url : '/rooms',
            type : 'POST',
            data : { foodId : String(this.value) },
            success:function(response){ $("html").load("/rooms");}
        });
    });
    $('input[type=radio][name=amenity]').change(function() {
        console.log("Selecting Amenity")
        req = $.ajax({
            url : '/rooms',
            type : 'POST',
            data : { amenitiesId : String(this.value) },
            success:function(response){ $("html").load("/rooms");}
        });
    });
});