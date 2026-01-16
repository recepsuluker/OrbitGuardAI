use pyo3::prelude::*;
use nalgebra::Vector3;
use rayon::prelude::*;

/// Satellite representation in 3D space
#[pyclass]
#[derive(Clone)]
pub struct Satellite {
    #[pyo3(get, set)]
    pub norad_id: i32,
    
    #[pyo3(get, set)]
    pub position: Vec<f64>,  // [x, y, z] in km
    
    #[pyo3(get, set)]
    pub velocity: Vec<f64>,  // [vx, vy, vz] in km/s
}

#[pymethods]
impl Satellite {
    #[new]
    fn new(norad_id: i32, position: Vec<f64>, velocity: Vec<f64>) -> PyResult<Self> {
        if position.len() != 3 || velocity.len() != 3 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Position and velocity must have 3 components"
            ));
        }
        
        Ok(Satellite {
            norad_id,
            position,
            velocity,
        })
    }
    
    /// Calculate distance to another satellite (km)
    fn distance_to(&self, other: &Satellite) -> f64 {
        let pos_self = Vector3::from_vec(self.position.clone());
        let pos_other = Vector3::from_vec(other.position.clone());
        (pos_self - pos_other).norm()
    }
    
    /// Calculate relative velocity (km/s)
    fn relative_velocity(&self, other: &Satellite) -> f64 {
        let vel_self = Vector3::from_vec(self.velocity.clone());
        let vel_other = Vector3::from_vec(other.velocity.clone());
        (vel_self - vel_other).norm()
    }
    
    /// Get current altitude above Earth surface (km)
    fn altitude(&self) -> f64 {
        const EARTH_RADIUS: f64 = 6371.0;  // km
        let pos = Vector3::from_vec(self.position.clone());
        pos.norm() - EARTH_RADIUS
    }
    
    /// Get orbital speed (km/s)
    fn speed(&self) -> f64 {
        let vel = Vector3::from_vec(self.velocity.clone());
        vel.norm()
    }
    
    fn __repr__(&self) -> String {
        format!(
            "Satellite(norad_id={}, alt={:.1}km, speed={:.2}km/s)",
            self.norad_id,
            self.altitude(),
            self.speed()
        )
    }
}

/// Conjunction event between two satellites
#[pyclass]
#[derive(Clone)]
pub struct Conjunction {
    #[pyo3(get)]
    pub norad_id_1: i32,
    
    #[pyo3(get)]
    pub norad_id_2: i32,
    
    #[pyo3(get)]
    pub distance_km: f64,
    
    #[pyo3(get)]
    pub relative_velocity_km_s: f64,
}

#[pymethods]
impl Conjunction {
    fn __repr__(&self) -> String {
        format!(
            "Conjunction({} ↔ {}, dist={:.2}km, rel_vel={:.2}km/s)",
            self.norad_id_1, self.norad_id_2, self.distance_km, self.relative_velocity_km_s
        )
    }
}

/// Find all close approaches between satellites (parallelized)
#[pyfunction]
fn find_conjunctions(satellites: Vec<Satellite>, threshold_km: f64) -> PyResult<Vec<Conjunction>> {
    if satellites.is_empty() {
        return Ok(Vec::new());
    }
    
    // Parallel conjunction detection using Rayon
    let conjunctions: Vec<Conjunction> = (0..satellites.len())
        .into_par_iter()
        .flat_map(|i| {
            (i + 1..satellites.len())
                .filter_map(|j| {
                    let sat1 = &satellites[i];
                    let sat2 = &satellites[j];
                    let dist = sat1.distance_to(sat2);
                    
                    if dist < threshold_km {
                        Some(Conjunction {
                            norad_id_1: sat1.norad_id,
                            norad_id_2: sat2.norad_id,
                            distance_km: dist,
                            relative_velocity_km_s: sat1.relative_velocity(sat2),
                        })
                    } else {
                        None
                    }
                })
                .collect::<Vec<_>>()
        })
        .collect();
    
    Ok(conjunctions)
}

/// Calculate pairwise distances between all satellites
#[pyfunction]
fn pairwise_distances(satellites: Vec<Satellite>) -> PyResult<Vec<Vec<f64>>> {
    let n = satellites.len();
    let mut distances = vec![vec![0.0; n]; n];
    
    for i in 0..n {
        for j in (i + 1)..n {
            let dist = satellites[i].distance_to(&satellites[j]);
            distances[i][j] = dist;
            distances[j][i] = dist;
        }
    }
    
    Ok(distances)
}

/// Find closest approach for each satellite
#[pyfunction]
fn find_closest_approaches(satellites: Vec<Satellite>) -> PyResult<Vec<(i32, i32, f64)>> {
    if satellites.len() < 2 {
        return Ok(Vec::new());
    }
    
    let results: Vec<(i32, i32, f64)> = (0..satellites.len())
        .into_par_iter()
        .map(|i| {
            let mut min_dist = f64::MAX;
            let mut closest_idx = 0;
            
            for j in 0..satellites.len() {
                if i != j {
                    let dist = satellites[i].distance_to(&satellites[j]);
                    if dist < min_dist {
                        min_dist = dist;
                        closest_idx = j;
                    }
                }
            }
            
            (
                satellites[i].norad_id,
                satellites[closest_idx].norad_id,
                min_dist,
            )
        })
        .collect();
    
    Ok(results)
}

/// Python module definition
#[pymodule]
fn orbit_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Satellite>()?;
    m.add_class::<Conjunction>()?;
    m.add_function(wrap_pyfunction!(find_conjunctions, m)?)?;
    m.add_function(wrap_pyfunction!(pairwise_distances, m)?)?;
    m.add_function(wrap_pyfunction!(find_closest_approaches, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_satellite_distance() {
        let sat1 = Satellite {
            norad_id: 1,
            position: vec![7000.0, 0.0, 0.0],
            velocity: vec![0.0, 7.5, 0.0],
        };
        
        let sat2 = Satellite {
            norad_id: 2,
            position: vec![7010.0, 0.0, 0.0],
            velocity: vec![0.0, 7.5, 0.0],
        };
        
        let dist = sat1.distance_to(&sat2);
        assert!((dist - 10.0).abs() < 0.001);
    }
    
    #[test]
    fn test_conjunction_detection() {
        let satellites = vec![
            Satellite {
                norad_id: 1,
                position: vec![7000.0, 0.0, 0.0],
                velocity: vec![0.0, 7.5, 0.0],
            },
            Satellite {
                norad_id: 2,
                position: vec![7005.0, 0.0, 0.0],
                velocity: vec![0.0, 7.5, 0.0],
            },
        ];
        
        let conjunctions = find_conjunctions(satellites, 10.0).unwrap();
        assert_eq!(conjunctions.len(), 1);
        assert_eq!(conjunctions[0].norad_id_1, 1);
        assert_eq!(conjunctions[0].norad_id_2, 2);
    }
}
