$(document).ready(function() {
    $("#togglePassword").click(function() {
      var input = $("#password");
      if (input.attr("type") === "password") {
        input.attr("type", "text");
      } else {
        input.attr("type", "password");
      }
    });
  });


  type="text/javascript"
        document.querySelector('form').addEventListener('submit', async function(event) {
            event.preventDefault();
    
            // Recoge los datos del formulario
            var formData = {
                'username': document.querySelector('#username-input').value,
                'password': document.querySelector('#password').value,
                'securityQuestion': document.querySelector('#securityQuestion').value,
                'securityAnswer': document.querySelector('#answer').value,
                'isAdmin': document.querySelector('#isAdmin').checked ? "1" : "0"
            };
    
            // Envia los datos al servidor
            try {
                const response = await fetch('/configuracion', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
    
                const data = await response.json();
    
                // Manejar la respuesta del servidor
                if (data.success) {
                    alert("Usuario creado con éxito");
                } else if (data.error) {
                    alert(data.error);
                }
            } catch (error) {
                // Manejar los errores en la solicitud
                alert("Hubo un problema al crear el usuario. Inténtalo de nuevo.");
            }
        });
    
async function fetchUsers() {
    // Reemplaza '/api/users' con tu endpoint Flask real
    const response = await fetch('/users');
    const users = await response.json();

    // Selecciona el cuerpo de la tabla
    const tableBody = document.getElementById('tableBody');

    // Limpia cualquier fila existente
    tableBody.innerHTML = '';

    // Agrega una nueva fila para cada usuario
    for (const user of users) {
        const row = document.createElement('tr');

        // Agrega una celda para cada propiedad del usuario
        for (const prop of ['id', 'username', 'registrationDate', 'analyzedSheets']) {
            const cell = document.createElement('td');
            if (prop === 'registrationDate') {
              cell.textContent = moment.utc(user[prop]).format('LL');
          } else {
              cell.textContent = user[prop];
          }
            row.appendChild(cell);
        }

        tableBody.appendChild(row);
    }
}


async function getUsername() {
    let response = await fetch('/get_username');
    let data = await response.json();
    document.getElementById('username').textContent = data.username;
  }

getUsername();
// Llama a la función fetchUsers cuando se cargue la página
document.addEventListener('DOMContentLoaded', fetchUsers);
