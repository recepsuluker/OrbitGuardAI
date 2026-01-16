"""
OrbitGuard AI - 3D Globe Visualization Component
Interactive 3D Earth with real-time satellite tracking using Three.js
"""

THREE_JS_GLOBE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: #000; }
        #globe-container { width: 100%; height: 600px; }
        #controls {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(10, 14, 26, 0.9);
            padding: 10px;
            border-radius: 8px;
            color: #e0e7ff;
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            border: 1px solid rgba(0, 245, 255, 0.3);
        }
        .control-item {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div id="globe-container"></div>
    <div id="controls">
        <div class="control-item">🖱️ Left Click: Rotate</div>
        <div class="control-item">🖱️ Scroll: Zoom</div>
        <div class="control-item">🛰️ Satellites: <span id="sat-count">0</span></div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script>
        // Scene setup
        const container = document.getElementById('globe-container');
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 10000);
        camera.position.z = 2.5;

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setClearColor(0x000000, 1);
        container.appendChild(renderer.domElement);

        // Earth
        const earthGeometry = new THREE.SphereGeometry(1, 64, 64);
        
        // Load Earth texture
        const textureLoader = new THREE.TextureLoader();
        const earthTexture = textureLoader.load('https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg');
        const bumpTexture = textureLoader.load('https://unpkg.com/three-globe/example/img/earth-topology.png');
        
        const earthMaterial = new THREE.MeshPhongMaterial({
            map: earthTexture,
            bumpMap: bumpTexture,
            bumpScale: 0.05,
            specular: new THREE.Color(0x333333),
            shininess: 5
        });
        
        const earth = new THREE.Mesh(earthGeometry, earthMaterial);
        scene.add(earth);

        // Atmosphere glow - monochrome white
        const glowGeometry = new THREE.SphereGeometry(1.05, 64, 64);
        const glowMaterial = new THREE.ShaderMaterial({
            uniforms: {
                c: { value: 0.2 },
                p: { value: 4.5 },
                glowColor: { value: new THREE.Color(0xffffff) },  // White glow
                viewVector: { value: camera.position }
            },
            vertexShader: `
                uniform vec3 viewVector;
                uniform float c;
                uniform float p;
                varying float intensity;
                void main() {
                    vec3 vNormal = normalize(normalMatrix * normal);
                    vec3 vNormel = normalize(normalMatrix * viewVector);
                    intensity = pow(c - dot(vNormal, vNormel), p);
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 glowColor;
                varying float intensity;
                void main() {
                    vec3 glow = glowColor * intensity;
                    gl_FragColor = vec4(glow, intensity * 0.6);
                }
            `,
            side: THREE.BackSide,
            blending: THREE.AdditiveBlending,
            transparent: true
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        scene.add(glow);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 1.5);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffffff, 1.0);
        sunLight.position.set(5, 3, 5);
        scene.add(sunLight);

        // Stars background
        const starsGeometry = new THREE.BufferGeometry();
        const starsMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.7,
            transparent: true
        });

        const starsVertices = [];
        for (let i = 0; i < 10000; i++) {
            const x = (Math.random() - 0.5) * 2000;
            const y = (Math.random() - 0.5) * 2000;
            const z = -Math.random() * 1000;
            starsVertices.push(x, y, z);
        }

        starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
        const stars = new THREE.Points(starsGeometry, starsMaterial);
        scene.add(stars);

        // Satellites array
        const satellites = [];
        const satelliteGroup = new THREE.Group();
        scene.add(satelliteGroup);

        // Function to add satellites
        function addSatellite(lat, lon, alt, name, isCritical = false) {
            // Convert lat/lon/alt to 3D position
            const radius = 1 + (alt / 6371); // Earth radius = 6371 km
            const phi = (90 - lat) * (Math.PI / 180);
            const theta = (lon + 180) * (Math.PI / 180);

            const x = -(radius * Math.sin(phi) * Math.cos(theta));
            const y = radius * Math.cos(phi);
            const z = radius * Math.sin(phi) * Math.sin(theta);

            // Satellite marker - monochrome (white/gray)
            const satGeometry = new THREE.SphereGeometry(0.01, 8, 8);
            const satMaterial = new THREE.MeshBasicMaterial({
                color: isCritical ? 0x888888 : 0xffffff,  // Gray for critical, white for normal
                emissive: isCritical ? 0x888888 : 0xffffff,
                emissiveIntensity: 0.8
            });
            const satMesh = new THREE.Mesh(satGeometry, satMaterial);
            satMesh.position.set(x, y, z);
            satMesh.userData = { name, lat, lon, alt };

            // Glow effect for satellite - monochrome
            const glowSatGeometry = new THREE.SphereGeometry(0.015, 16, 16);
            const glowSatMaterial = new THREE.MeshBasicMaterial({
                color: isCritical ? 0x888888 : 0xffffff,
                transparent: true,
                opacity: 0.4
            });
            const glowSatMesh = new THREE.Mesh(glowSatGeometry, glowSatMaterial);
            glowSatMesh.position.copy(satMesh.position);
            
            satelliteGroup.add(satMesh);
            satelliteGroup.add(glowSatMesh);

            satellites.push({ mesh: satMesh, glow: glowSatMesh, data: { name, lat, lon, alt } });
        }

        // Mouse interaction
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let rotation = { x: 0, y: 0 };

        container.addEventListener('mousedown', () => isDragging = true);
        container.addEventListener('mouseup', () => isDragging = false);
        container.addEventListener('mouseleave', () => isDragging = false);

        container.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const deltaX = e.clientX - previousMousePosition.x;
                const deltaY = e.clientY - previousMousePosition.y;

                rotation.y += deltaX * 0.005;
                rotation.x += deltaY * 0.005;
            }

            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        // Zoom
        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            camera.position.z += e.deltaY * 0.001;
            camera.position.z = Math.max(1.5, Math.min(5, camera.position.z));
        });

        // Animation loop
        function animate() {
            requestAnimationFrame(animate);

            // Auto-rotate if not dragging
            if (!isDragging) {
                earth.rotation.y += 0.001;
                satelliteGroup.rotation.y += 0.001;
            } else {
                earth.rotation.y = rotation.y;
                earth.rotation.x = rotation.x;
                satelliteGroup.rotation.y = rotation.y;
                satelliteGroup.rotation.x = rotation.x;
            }

            // Pulse satellites
            satellites.forEach(sat => {
                const scale = 1 + Math.sin(Date.now() * 0.003) * 0.2;
                sat.glow.scale.set(scale, scale, scale);
            });

            renderer.render(scene, camera);
        }

        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Start animation
        animate();

        // Expose function to Python
        window.updateSatellites = function(satellitesData) {
            // Clear existing satellites
            satellites.forEach(sat => {
                satelliteGroup.remove(sat.mesh);
                satelliteGroup.remove(sat.glow);
            });
            satellites.length = 0;

            // Add new satellites
            satellitesData.forEach(sat => {
                addSatellite(sat.lat, sat.lon, sat.alt, sat.name, sat.critical || false);
            });

            document.getElementById('sat-count').textContent = satellitesData.length;
        };

        // Initial satellites (will be replaced by Python data)
        window.updateSatellites([
            { lat: 0, lon: 0, alt: 400, name: 'Test Sat 1', critical: false },
            { lat: 45, lon: 90, alt: 550, name: 'Test Sat 2', critical: true }
        ]);
    </script>
</body>
</html>
"""


def create_3d_globe_html(satellites_data):
    """
    Create HTML for 3D globe with satellite data
    
    Args:
        satellites_data: List of dicts with keys: name, lat, lon, alt, critical
    
    Returns:
        HTML string ready to embed in Streamlit
    """
    import json
    
    # Debug: print satellite count
    print(f"[DEBUG] Creating globe with {len(satellites_data)} satellites")
    
    # Convert satellites to JSON
    sats_json = json.dumps(satellites_data)
    
    # Create complete HTML with data injected
    html_with_data = THREE_JS_GLOBE_HTML.replace(
        "// Initial satellites (will be replaced by Python data)\n        window.updateSatellites([",
        f"// Initial satellites (from Python data)\n        console.log('Loading satellites:', {sats_json});\n        window.updateSatellites({sats_json}); /* old test data: ["
    ).replace(
        "        ]);\n    </script>",
        "        ]); */\n    </script>"
    )
    
    return html_with_data
