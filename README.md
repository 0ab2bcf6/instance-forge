# instance-forge
This repository contains a flexible and extensible framework for generating, and solving instances of common scheduling problems such as Flow Shop, Job Shop, and Open Shop. It provides a structured instance representation, solver interfaces, and basic solvers, making it a powerful foundation for research and development in scheduling optimization.

# TODO
- **WORK IN PROGRESS**: This code is not working yet; it's work in progress `:).txt`
- **alpha fields**: Add Flexible Flowshop (FFc) (Hybrid Flowshop) and Flexible Jobshop (FJc) to the Alpha Fields and adjust classes accordingly. This will require design work and changes in `instance.py`
- **beta fields**: Add explicit precedence constraints and adjust logic in `instance.py` to generate the constraints accordingly
- **solver interfaces**: As for now, there's not a single solver interface in this repository
- **problem satisfiability**: It reamins to see wether the generated instances are solvable or not