const wavelengths = [
    410, 435, 460, 485, 510, 535, 560, 585, 645, 660, 690, 720, 740, 760, 810, 860, 900, 940
];

let modelSaved = false;

function checkModelSaved() {
if (!modelSaved) {
    document.getElementById("alertBox").style.visibility = 'visible';
    return false;
}
return true;
}

let nombreModelo = '';
async function enviarModelo() {
nombreModelo = document.getElementById('nombreModelo').value;

if (!nombreModelo) {
    alert('Por favor, introduce el nombre del modelo.');
    return;
}

try {
    const response = await fetch('/guardar_modelo', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ nombreModelo })
    });
    if (!response.ok) {
        throw new Error('Error en la solicitud HTTP');
    }
    const data = await response.json();
    if (data.error) {
        throw new Error(data.error);
    }
    alert('Modelo guardado correctamente');
    modelSaved = true;
} catch (error) {
    console.error('Error:', error);
    alert('Error al guardar el modelo');
}
}


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
  // ...
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
    if (!checkModelSaved()) return;
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
    if (!checkModelSaved()) return;
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

async function trainModel() {
    document.getElementById('loader').style.display = 'block'; // Muestra el loader

    // Realiza la petición al servidor para entrenar el modelo.
    const response = await fetch(`/train_model/${nombreModelo}`, { method: 'POST' });

    // Verifica si la petición fue exitosa
    if (response.ok) {
        alert('El entrenamiento se completó con éxito');
    } else {
        alert('Error durante el entrenamiento');
    }

    document.getElementById('loader').style.display = 'none'; // Oculta el loader una vez completado el entrenamiento
}

async function getUsername() {
    let response = await fetch('/get_username');
    let data = await response.json();
    document.getElementById('username').textContent = data.username;
  }


  let selectedHojaId;

        async function fetchHojas() {
            try {
                const response = await fetch('/hojas');
                const hojas = await response.json();
                return hojas;
            } catch (error) {
                console.error('Error:', error);
                }
             }
                
        
        async function displayHojas() {
            const hojasTableBody = document.getElementById('hojasTableBody');
            const hojas = await fetchHojas();

            hojasTableBody.innerHTML = '';

            hojas.forEach(hoja => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${hoja.HojaId}</td>
                    <td>${hoja.Longitud}</td>
                    <td>${hoja.Ancho}</td>
                    <td>${moment.utc(hoja.Fecha).format('LL')}</td>
                `;
                row.addEventListener('click', () => {
                    selectedHojaId = hoja.HojaId;
                    const rows = hojasTableBody.getElementsByTagName('tr');
                    for (let i = 0; i < rows.length; i++) {
                        rows[i].classList.remove('table-active');
                    }
                    row.classList.add('table-active');
                });

                hojasTableBody.appendChild(row);
            });
        }     

        async function loadSelectedHojaData() {
            if (!selectedHojaId) {
                alert('Seleccione una hoja antes de cargar información.');
                return;
            }

            // Lógica para cargar información de la hoja seleccionada
            try {
                // Cargar la imagen procesada
                showProcessedImage(selectedHojaId);

                // Cargar los datos de las 18 bandas
                const response = await fetch(`/get_hoja_data/${selectedHojaId}`);
                const hojaData = await response.json();
                const hojaValues = hojaData.map(item => item.Valor);
                chart.data.datasets[0].data = hojaValues;
                chart.update();
            } catch (error) {
                console.error('Error:', error);
            }

            $('#hojasModal').modal('hide');
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


getUsername();