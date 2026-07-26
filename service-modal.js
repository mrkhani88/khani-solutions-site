const serviceModalDetails = {
  calls: {
    title: "MRI AI",
    description: "AI-assisted segmentation of brain, spinal cord, and nerve-root anatomy from MRI.",
    what: "A medical-imaging pipeline that converts MRI datasets into labeled anatomical regions for engineering analysis.",
    how: "The workflow reads MRI data, segments defined anatomy, runs quality checks, and prepares each region for downstream geometry generation.",
    help: "Reduces repetitive image processing and creates a consistent starting point for patient-specific simulation.",
  },
  texts: {
    title: "STL Geometry",
    description: "Simulation-ready surface geometry generated from segmented anatomy or engineering data.",
    what: "An automated conversion pipeline that transforms labeled image regions into organized STL surface models.",
    how: "Segmented masks are converted, repaired, smoothed, labeled, and checked for the topology required by the next modeling stage.",
    help: "Produces traceable geometry without rebuilding every case by hand and keeps anatomical regions consistent across projects.",
  },
  email: {
    title: "Automated Meshing",
    description: "Computational meshes generated from complex STL geometry with repeatable quality controls.",
    what: "A meshing workflow for biomedical, thermal, and fluid domains that prepares cases for CFD or coupled analysis.",
    how: "The platform applies region-specific mesh rules, creates the volume mesh, checks quality metrics, and packages solver-ready files.",
    help: "Shortens setup time, improves consistency between cases, and makes large simulation studies practical.",
  },
  invoices: {
    title: "CSF Flow",
    description: "Patient-specific cerebrospinal fluid simulation through the brain and spinal canal.",
    what: "A CFD model of physiologic CSF motion using MRI-derived anatomy and subject-specific or literature-based boundary conditions.",
    how: "The workflow prepares anatomy, mesh, cardiac and respiratory forcing, fluid properties, solver settings, and result processing.",
    help: "Reveals local flow, mixing, pressure, and transport behavior that cannot be measured throughout the full CNS directly.",
  },
  schedule: {
    title: "Drug Transport",
    description: "Multiphase and particle-based modeling of therapeutics delivered within the central nervous system.",
    what: "A simulation framework for studying how formulation density, infusion location, protocol, physiology, and posture affect distribution.",
    how: "The model combines CSF flow with injection conditions, multiphase transport, particle tracking, dynamic mesh, and quantitative reporting.",
    help: "Supports protocol comparison, device development, and evidence-based decisions before costly experimental studies.",
  },
  leads: {
    title: "Digital Twins",
    description: "Patient-specific computational models that connect anatomy, physiology, devices, and therapy.",
    what: "A digital representation of an individual CNS geometry and its relevant fluid and transport behavior.",
    how: "Imaging, boundary conditions, material properties, devices, and treatment protocols are assembled into a reproducible simulation case.",
    help: "Enables consistent comparison across patients, devices, formulations, and treatment scenarios.",
  },
  website: {
    title: "Thermal Engineering",
    description: "Multi-fidelity thermal analysis for batteries, cooling systems, and coupled hardware.",
    what: "Python-based 0D, 1D, 2D, and 3D models for heat generation, conduction, convection, coolant networks, and component temperatures.",
    how: "The right model fidelity is selected for the decision, then inputs, solvers, visualization, and reporting are connected in one app.",
    help: "Speeds design trade studies and exposes temperature limits, cooling bottlenecks, and system-level interactions.",
  },
  listings: {
    title: "Computational Fluid Dynamics",
    description: "High-fidelity fluid and heat-transfer analysis for complex engineering systems.",
    what: "CFD models for turbulent, multiphase, compressible, conjugate heat-transfer, dynamic-mesh, and particle-transport problems.",
    how: "Physics, geometry, mesh, solver strategy, convergence, and post-processing are selected around the engineering question.",
    help: "Provides detailed flow and thermal insight for designs where testing alone is slow, expensive, or incomplete.",
  },
  reviews: {
    title: "Verification & Validation",
    description: "Engineering checks that make automated simulation results defensible.",
    what: "A structured validation layer for mesh independence, conservation, convergence, sensitivity, benchmark, and experimental comparison.",
    how: "Acceptance criteria and traceable checks are built into the workflow so every case produces evidence alongside results.",
    help: "Makes errors easier to detect and gives engineers a clear basis for trusting, reviewing, and communicating predictions.",
  },
  reports: {
    title: "Engineering Platforms",
    description: "Scientific software that connects data, simulation, visualization, and reporting.",
    what: "A custom platform that turns an expert engineering procedure into a guided, repeatable tool for a team.",
    how: "Python, web interfaces, CFD solvers, HPC resources, data management, and automated reports are integrated around the actual workflow.",
    help: "Moves engineering knowledge out of disconnected scripts and manual handoffs into a scalable system your team can operate.",
  },
};

const serviceModal = document.querySelector("[data-service-modal]");
const serviceModalPanel = document.querySelector(".service-modal__panel");
const serviceModalTitle = document.querySelector("#service-modal-title");
const serviceModalDescription = document.querySelector("#service-modal-description");
const serviceModalWhat = document.querySelector("[data-service-what]");
const serviceModalHow = document.querySelector("[data-service-how]");
const serviceModalHelp = document.querySelector("[data-service-help]");

function openServiceModal(serviceKey) {
  const detail = serviceModalDetails[serviceKey];
  if (!detail || !serviceModal) return;
  serviceModalTitle.textContent = detail.title;
  serviceModalDescription.textContent = detail.description;
  serviceModalWhat.textContent = detail.what;
  serviceModalHow.textContent = detail.how;
  serviceModalHelp.textContent = detail.help;
  serviceModal.hidden = false;
  window.requestAnimationFrame(() => serviceModalPanel?.focus?.());
}

function closeServiceModal() {
  if (serviceModal) serviceModal.hidden = true;
}

document.querySelectorAll("[data-service]").forEach((tile) => {
  tile.addEventListener("click", () => openServiceModal(tile.dataset.service));
  tile.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openServiceModal(tile.dataset.service);
  });
});

document.querySelectorAll("[data-service-close]").forEach((control) => {
  control.addEventListener("click", closeServiceModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && serviceModal && !serviceModal.hidden) {
    event.preventDefault();
    closeServiceModal();
  }
});
