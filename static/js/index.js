async function getTotales() {
    let response = await fetch('/get_totales');
    let data = await response.json();
  
    var ctx = document.getElementById('myChart1').getContext('2d');
  
    // Define array of colors
    let colors = [
      'rgba(75, 192, 192, 0.2)',
      'rgba(255, 99, 132, 0.2)',
      'rgba(54, 162, 235, 0.2)',
      'rgba(255, 206, 86, 0.2)',
      'rgba(153, 102, 255, 0.2)',
      // Add more colors if there are more categories
    ];
  
    // Apply a color to each category
    let backgroundColors = data.map((item, index) => colors[index % colors.length]);
  
    new Chart(ctx, {
      type: 'pie',
      data: {
          labels: data.map(item => item.Descripcion),
          datasets: [{
              label: '# de Hojas',
              data: data.map(item => item.Total),
              backgroundColor: backgroundColors,
              borderColor: 'rgba(0, 0, 0, 1)',
              borderWidth: 1
          }]
      },
      options: {
        title: {
          display: true,
          text: 'Totales por Categoría'
        }
      }
    });
  }
  
  
    // Assuming you have a '/get_username' route that returns the username
    async function getUsername() {
      let response = await fetch('/get_username');
      let data = await response.json();
      document.getElementById('username').textContent = data.username;
    }

    // Las longitudes de onda son fijas, las ponemos aquí
    const wavelengths = [410, 435, 460, 485, 510, 535, 560, 585, 610, 645, 660, 690, 720, 740, 760, 810, 860, 900, 940];

    async function fetchData() {
        try {
            const response = await fetch("/average_band_values");  // reemplaza con la ruta correcta a tu endpoint
            const data = await response.json();
            drawChart(data);
        } catch (error) {
            console.error("Error: ", error);
        }
    }
    
    function drawChart(data) {
      // Configuración del gráfico
      var container = document.getElementById('chartContainer');  // Obtiene el contenedor
      var svgWidth = container.offsetWidth;  // Usa el ancho del contenedor
      var svgHeight = 265;  // Puedes ajustar la altura si es necesario
      var margin = {top: 20, right: 20, bottom: 50, left: 50};
      var width = svgWidth - margin.left - margin.right;
      var height = svgHeight - margin.top - margin.bottom;

      // Crear el elemento SVG
      var svg = d3.select("#lineChart")
          .attr('width', svgWidth)
          .attr('height', svgHeight);
    
      var g = svg.append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    
      // Configurar las escalas y los ejes
      var x = d3.scaleLinear()
        .domain(d3.extent(wavelengths))
        .range([0, width]);

        g.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x).tickValues(wavelengths))
        .selectAll("text")  
            .style("text-anchor", "end")
            .attr("dx", "-.8em")
            .attr("dy", ".15em")
            .attr("transform", "rotate(-65)") 
        .select(".domain")
        .remove();
      var y = d3.scaleLinear().range([height, 0]);
    
      var line = d3.line()
          .x(function(d) { return x(d.wavelength); })
          .y(function(d) { return y(d.value); });
    
      // Definir la escala de color aquí
      var color = d3.scaleOrdinal(d3.schemeCategory10);
    
      // Filtrar los datos para excluir las categorías con valores vacíos
      var filteredData = data.filter(c => c.values.length > 0);
    
      x.domain(d3.extent(wavelengths));
      y.domain([
        d3.min(filteredData, function(c) { return d3.min(c.values, function(d) { return d.value; }); }),
        d3.max(filteredData, function(c) { return d3.max(c.values, function(d) { return d.value; }); })
    ]);
      
      
      g.append("text")
      .attr("transform", "translate(" + (width/2) + " ," + (height + 45) + ")")  // Posiciona el texto
      .style("text-anchor", "middle")  // Centra el texto
      .text("Longitudes");

      g.append("g")
          .call(d3.axisLeft(y))
          .append("text")
          .attr("fill", "#000")
          .attr("transform", "rotate(-90)")
          .attr("y", -40)  // Cambia este valor para mover la etiqueta
          .attr("dy", "0.71em")
          .attr("text-anchor", "end")
          .style("font-size", "15px")  // Establece el tamaño de la fuente a 15px
          .text("Reflectancia");
    
      // Dibujar las líneas
      filteredData.forEach(function(c) {
      
        g.append("path")
            .datum(c.values)
            .attr("class", "line")
            .attr("d", line)
            .style("fill","none")
            .style("stroke", function() { return color(c.category); })
            .style("stroke-width", 1.5);  // Ajusta esto al grosor deseado
    });
    
    var legendSpace = width / filteredData.length;  // Espaciado para la leyenda

    filteredData.forEach(function(d,i) {
        svg.append("text")
            .attr("x", margin.left + (i*legendSpace))  // Posicion horizontal de la leyenda
            .attr("y", margin.top -10)  // Posicion vertical de la leyenda
            .attr("class", "legend")    // Estilo de la leyenda
            .style("fill", function() {  // Color de la leyenda
                return color(d.category);
            })
            .style("font-size", "12px")  // Ajusta el tamaño de la fuente de la leyenda
            .text(d.category);
    });

    }
    async function fetchDatag3() {
      try {
          const response = await fetch("/hojas_data");
          const data = await response.json();
          drawBoxPlot(data);
      } catch (error) {
          console.error("Error: ", error);
      }
  }
  
  function drawBoxPlot(data) {
      const categories = data.map(d => d.categoria);
      const longitudData = data.map(d => d.longitud);
      const anchoData = data.map(d => d.ancho);
      const areaData = data.map(d => d.area);
  
      var ctx = document.getElementById('boxPlotChart').getContext('2d');
      new Chart(ctx, {
          type: 'boxplot',
          data: {
              labels: categories,
              datasets: [{
                  label: 'Longitud',
                  data: longitudData,
                  backgroundColor: 'rgba(255, 99, 132, 0.5)',
                  borderColor: 'rgba(255, 99, 132, 1)',
                  borderWidth: 1
              }, {
                  label: 'Ancho',
                  data: anchoData,
                  backgroundColor: 'rgba(54, 162, 235, 0.5)',
                  borderColor: 'rgba(54, 162, 235, 1)',
                  borderWidth: 1
              }, {
                  label: 'Area',
                  data: areaData,
                  backgroundColor: 'rgba(255, 206, 86, 0.5)',
                  borderColor: 'rgba(255, 206, 86, 1)',
                  borderWidth: 1
              }]
          },
          options: {
              responsive: true,
              legend: {
                  position: 'top',
              },
              title: {
                  display: true,
                  text: 'Distribución de Características de las Hojas por Categoría'
              }
          }
      });
  }

  let timeChart;  // Declarar el gráfico globalmente para poder actualizarlo más tarde
  async function fetchDataAndUpdateChart() {
    moment.locale('es');
    let interval = document.getElementById('timeInterval').value;
    
    let response = await fetch(`/hojas_por_intervalo?intervalo=${interval}`);
    let data = await response.json();
    
    console.log(data);
    // Mapear los datos en arreglos de fechas y cantidades, y luego invertirlos
    let fechas = data.map(item => {
        // Crear un objeto de fecha moment.js
        let fecha = moment(item.Fecha);
        
        // Formatear la fecha dependiendo del intervalo
        switch(interval) {
            case "dia":
                return fecha.format('dddd');  // Devuelve el nombre del día de la semana (p.ej., 'Lunes')
            case "semana":
                return "S" + fecha.format('WW');  // Devuelve 'S26' para la semana 26 del año
            case "mes":
                return fecha.format('MMM');  // Devuelve el nombre abreviado del mes (p.ej., 'Jul')
        }
    }).reverse();
    let cantidades = data.map(item => item.Cantidad).reverse();
    
    // Aquí actualizas los datos y las etiquetas de tu gráfico
    timeChart.data.labels = fechas;
    timeChart.data.datasets[0].data = cantidades;
    timeChart.update();
}




window.onload = async function() {
  let ctx = document.getElementById('timeChart').getContext('2d');

  timeChart = new Chart(ctx, {
      type: 'bar',
      data: {
          labels: [],
          datasets: [{
              label: '# de hojas analizadas',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              borderColor: 'rgba(75, 192, 192, 1)',
              borderWidth: 1,
              data: []
          }]
      },
      options: {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero: true
                  }
              }]
          }
      }
  });

  await fetchDataAndUpdateChart();  // Cargar datos inicialmente cuando la página se carga

  document.getElementById('timeInterval').addEventListener('change', fetchDataAndUpdateChart);  // Actualizar cuando se cambia el intervalo
}

$(document).ready(function() {
    var table = $('#hojasTable').DataTable();

    async function loadHojas() {
        const response = await fetch('/hojas');
        const data = await response.json();
        
        data.forEach(hoja => {
            table.row.add([
                hoja.HojaId,
                hoja.Longitud,
                hoja.Ancho,
                hoja.Area,
                hoja.Descripcion,
                hoja.modelo,
                hoja.username,
                moment.utc(hoja.Fecha).format('LL')
            ]).draw(false);
        });

        $('#hojasTable tbody').on('click', 'tr', function () {
            const data = table.row(this).data();
            selectedHojaId = data[0];
            loadSelectedHojaData();
        });
    }

    loadHojas();
});

$(document).ready(function() {
    $.get("/get_admin", function(data, status){
        // data will be true if the user is admin, and false otherwise
        console.log(data);
        if (data === false) {
            // Disable the buttons
            $("#entrenamiento").addClass("disabled");
            $("#reporteria").addClass("disabled");
            $("#configuracion").addClass("disabled");
        }
    });
});


  fetchDatag3();
  
  
    
    // Llamar a la función para obtener los datos y dibujar el gráfico
    fetchData();
  
    getTotales();
    getUsername();