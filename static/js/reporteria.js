let username;
async function getUsername() {
    let response = await fetch('/get_username');
    let data = await response.json();
    document.getElementById('username').textContent = data.username;
    username = data.username;
  }

document.addEventListener('DOMContentLoaded', (event) => {
    // Manejar cambios en el tipo de informe
    document.getElementById('reportType').addEventListener('change', async function() {
        var reportType = this.value;
        
        // Limpiar el contenedor de opciones de informe
        document.getElementById('reportOptionsContainer').innerHTML = '';
        document.getElementById('fieldOptionsContainer').classList.add('d-none');
        document.getElementById('dateRangeContainer').classList.add('d-none');

        // Añadir las opciones de informe apropiadas para el tipo de informe seleccionado
        // Aquí debes hacer las llamadas a la API para obtener las opciones de informe apropiadas para cada tipo de informe
        if (reportType == 'category') {
            // Añadir opciones de informe para informes de categoría
            addCategoryReportOptions();

            // Aquí puedes usar la data para rellenar tus opciones de informe
            // (modifica esto para incluir las opciones de informe que necesites)

        } else if (reportType == 'model') {
          
            document.getElementById('dateRangeContainer').classList.remove('d-none');
            


        } else if (reportType == 'band') {
            // Añadir opciones de informe para informes de banda
            const response = await fetch('ruta/api/bandas');
            const data = await response.json();

            // Aquí puedes usar la data para rellenar tus opciones de informe
            // (modifica esto para incluir las opciones de informe que necesites)

        } else if (reportType == 'user') {
            // Añadir opciones de informe para informes de usuario
            const response = await fetch('ruta/api/usuarios');
            const data = await response.json();

            // Aquí puedes usar la data para rellenar tus opciones de informe
            // (modifica esto para incluir las opciones de informe que necesites)
        }

        if (reportType != 'Seleccione...') {
            document.getElementById('fieldOptionsContainer').classList.remove('d-none');
            document.getElementById('dateRangeContainer').classList.remove('d-none');
        }
    });

    // Manejar clic en el botón "Generar Informe"
    document.getElementById('generateReportButton').addEventListener('click', async function() {
        var reportType = document.getElementById('reportType').value;
        if (reportType == 'category') {
            // Generar informe de categoría
            await generateCategoryReport();
        }else if (reportType == 'model'){
            generateModelReport();
        }

        
    });
});

async function addCategoryReportOptions() {
    // Realizar una llamada a la API para obtener las categorías
    const response = await fetch('/categorias');
    const data = await response.json();

    // Crea un select y lo añade al contenedor de opciones de informe
    var selectElement = document.createElement('select');
    selectElement.id = 'categoryOptions';
    document.getElementById('reportOptionsContainer').appendChild(selectElement);

    // Añadir una opción de informe para cada categoría
    data.forEach(function(categoria) {
        var optionElement = document.createElement('option');
        optionElement.value = categoria.IdCategoria;
        optionElement.textContent = categoria.Descripcion;
        selectElement.appendChild(optionElement);
    });
}

async function generateCategoryReport() {
    // Obtener las fechas de inicio y fin seleccionadas
    var startDate = document.getElementById('startDate').value;
    var endDate = document.getElementById('endDate').value;
    window.jsPDF = window.jspdf.jsPDF;
    // Obtener los campos de interés seleccionados
    var fields = Array.from(document.getElementById('fieldOptions').selectedOptions).map(function(option) {
        return option.value;
    });

    // Obtener la categoría seleccionada
    var category = document.getElementById('categoryOptions').value;

    // Realizar una llamada a la API para generar el informe
    const response = await fetch(`informes_categoria?start_date=${startDate}&end_date=${endDate}&category=${category}`);
    const report = await response.json();

    // Generar el PDF
    const doc = new jsPDF();
    
    const title = 'Reporte de la Categoría';
    doc.setFontSize(22);
    doc.text(title, 20, 20);
    doc.setFontSize(16);
    doc.text(`Generado por: ${username}`, 20, 30);
    doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 20, 40);
    doc.text(`Categoría: ${category}`, 20, 50);
    doc.text(`Intervalo de tiempo: Desde ${startDate} hasta ${endDate}`, 20, 60);

    // Reestructuramos 'report' para que sea una estructura que pueda ser usada por autotable
    let data = [];

    const keys = ["min", "q1", "median", "q3", "max"];
    keys.forEach((key) => {
        let row = { "Propiedad": key };
        Object.keys(report[0]).forEach((header) => {
            if (header !== "categoria") {
                row[header] = report[0][header][key] || "";
            }
        });
        data.push(row);
    });

    const columns = Object.keys(data[0]).map(key => ({ title: key, dataKey: key }));

    doc.autoTable(columns, data, { startY: 70 });
    var finalY = doc.autoTable.previous.finalY;

    let adjustedReport = report.map(item => ({
        ancho: [item.ancho.min, item.ancho.q1, item.ancho.median, item.ancho.q3, item.ancho.max],
        longitud: [item.longitud.min, item.longitud.q1, item.longitud.median, item.longitud.q3, item.longitud.max],
        area: [item.area.min, item.area.q1, item.area.median, item.area.q3, item.area.max],
        categoria: item.categoria
    }));

    // Dibujar el gráfico
    await drawBoxPlot(adjustedReport);

// Convertir el gráfico a imagen y agregarla al PDF
    var canvas = document.getElementById('boxPlotChart');
    var imgData = canvas.toDataURL("image/png");

    doc.addImage(imgData, 'PNG', 10, finalY + 10, 180, 160);
    doc.save('report.pdf');

    // Mostrar el informe
    console.log(report);
}

function drawBoxPlot(data) {
    return new Promise((resolve, reject) => {
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
                },
                animation: {
                    onComplete: function() {
                        resolve();
                    }
                }
            }
        });
    });
}






async function generateModelReport() {
    // Obtener las fechas de inicio y fin seleccionadas
    var startDate = document.getElementById('startDate').value;
    var endDate = document.getElementById('endDate').value;
    window.jsPDF = window.jspdf.jsPDF;

    // Obtener los campos de interés seleccionados
    var fields = Array.from(document.getElementById('fieldOptions').selectedOptions).map(function(option) {
        return option.value;
    });

    // Realizar una llamada a la API para generar el informe
    const response = await fetch(`informes_modelo?start_date=${startDate}&end_date=${endDate}`);
    const report = await response.json();

    // Generar el PDF
    const doc = new jsPDF();
    
    const title = 'Reporte del Modelo';
    doc.setFontSize(22);
    doc.text(title, 20, 20);
    doc.setFontSize(16);
    doc.text(`Generado por: ${username}`, 20, 30);
    doc.text(`Fecha: ${new Date().toLocaleDateString()}`, 20, 40);
    doc.text(`Intervalo de tiempo: Desde ${startDate} hasta ${endDate}`, 20, 60);

    // Crear la tabla en el PDF
    doc.autoTable({
        startY: 70,
        head: [['Nombre', 'Fecha', 'Entrenamientos', 'Creado Por:', 'Hojas Analizadas', 'Precisión']],
        body: report.map(function(modelo) {
            return [
                modelo.nombre,
                modelo.fecha,
                modelo.entrenamientos,
                modelo.usuario,
                modelo.hojas,
                modelo.precision,
            ];
        }),
    });

    // Guardar y mostrar el PDF

    console.log(report)
    doc.save('reporte_modelo.pdf');
}





getUsername();


