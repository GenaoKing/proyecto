const wavelengths = [
    410, 435, 460, 485, 510, 535, 560, 585, 645, 660, 690, 720, 740, 760, 810, 860, 900, 940
];

function getBarColor(wavelength) {
    if (wavelength >= 410 && wavelength <= 485) {
        return 'rgba(127, 0, 255, 0.4)'; // Ultravioleta
    } else if (wavelength >= 510 && wavelength <= 760) {
        return 'rgba(255, 255, 255, 0.4)'; // Blanco
    } else {
        return 'rgba(255, 0, 0, 0.4)'; // Infrarrojo
    }
}

function getBorderColor(wavelength) {
    if (wavelength >= 410 && wavelength <= 485) {
        return 'rgba(127, 0, 255, 1)'; // Ultravioleta
    } else if (wavelength >= 510 && wavelength <= 760) {
        return 'rgba(255, 255, 255, 1)'; // Blanco
    } else {
        return 'rgba(255, 0, 0, 1)'; // Infrarrojo
    }
}

const chartElement = document.getElementById('barChart');

const chart = new Chart(chartElement, {
    type: 'bar',
    data: {
        labels: wavelengths.map(wavelength => `${wavelength} nm`),
        datasets: [
            {
                label: 'Valor',
                data: [],
                backgroundColor: wavelengths.map(getBarColor),
                borderColor: wavelengths.map(getBorderColor),
                borderWidth: 1
            }
        ]
    },
    options: {
        plugins: {
            legend: {
                labels: {
                    generateLabels: function (chart) {
                        return [{
                            text: 'UV',
                            fillStyle: 'rgba(127, 0, 255, 1)',
                            strokeStyle: 'rgba(127, 0, 255, 1)',
                            lineWidth: 1
                        },
                        {
                            text: 'BL',
                            fillStyle: 'rgba(255, 255, 255, 1)',
                            strokeStyle: 'rgba(255, 255, 255, 1)',
                            lineWidth: 1
                        },
                        {
                            text: 'IR',
                            fillStyle: 'rgba(255, 0, 0, 1)',
                            strokeStyle: 'rgba(255, 0, 0, 1)',
                            lineWidth: 1
                        }];
                    }
                }
            }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Longitud de onda'
                }
            },
            y: {
                beginAtZero: true
            }
        }
    }
});

async function updateData() {
    try {
        const response = await fetch('http://192.168.43.138:8080/sensor_data');
        const data = await response.json();

        chart.data.datasets[0].data = data;
        chart.update();
        fetchLatestHojaIdAndShowImage();
    } catch (error) {
        console.error('Error:', error);
    }
}

let pollingIntervalId;

async function setFlag() {
    try {
        // Obtiene el valor seleccionado del combobox
        const categoriaId = document.getElementById('categoriaSelect').value;

        // Enviar el valor del combobox con la solicitud de captura
        const response = await fetch('http://192.168.43.138:8080/set_flag', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({categoriaId: categoriaId})
        });

        // Verifica si la respuesta es 200 (exitosa)
        if (response.ok) {
            console.log('Bandera establecida');

            // Llama a la función para obtener y mostrar la última imagen
            pollingIntervalId = setInterval(checkIfProcessingIsDone, 3000);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function checkIfProcessingIsDone() {
    try {
        const response = await fetch('/ready');

        if (response.ok) {
            console.log('Imagen procesada correctamente');

            // Llama a la función para obtener y mostrar la última imagen
            updateData();

            // Interrumpe el polling
            clearInterval(pollingIntervalId);
        } else {
            console.log('El procesamiento de la imagen aún no ha terminado');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function showProcessedImage(HojaId) {
    const processedImage = document.getElementById('processed_image');
    processedImage.src = `static/image_${HojaId}.jpg?${new Date().getTime()}`;
}

async function fetchLatestHojaIdAndShowImage() {
    try {
        const response = await fetch('/get_latest_hoja_id');
        const HojaId = await response.json();
        showProcessedImage(HojaId);
    } catch (error) {
        console.error('Error:', error);
    }
}


async function getModelsAndFillCombobox() {
    const response = await fetch('/get_models');
    const models = await response.json();

    const modelSelect = document.getElementById('modelSelect');
    models.forEach((model) => {
        const option = document.createElement('option');
        option.value = model.id;
        option.text = model.descripcion;
        modelSelect.appendChild(option);
    });
}

// Llama a la función cuando la página carga
window.onload = getModelsAndFillCombobox;

async function getUsername() {
    let response = await fetch('/get_username');
    let data = await response.json();
    document.getElementById('username').textContent = data.username;
  }

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

  async function capture(){
    var modelSelect = document.getElementById('modelSelect');
    var selectedModel = modelSelect.value;
    var selectedname = modelSelect.options[modelSelect.selectedIndex].text;

    var data = {
        model: selectedModel,
        name: selectedname,
        capture: true
    };


    console.log(data);

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        pollingIntervalId = setInterval(checkIfProcessingIsDone, 3000);
        const jsonData = await response.json();
        // Haz algo con jsonData, la respuesta del servidor
    } catch (error) {
        console.log('Error:', error);
    }
}





getUsername();
