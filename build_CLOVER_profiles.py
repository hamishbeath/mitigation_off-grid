# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

"""
===============================================================================
            Scripts for preparing datasets for CLOVER modelling
            
===============================================================================
            Created: October 2021 
===============================================================================
Author:
    Hamish Beath
===============================================================================
"""
class build_inputs():
    def __init__(self):
        self.data_filepath = '~/Library/Mobile Documents/com~apple~CloudDocs/Mitigation_project/DATA/'
        self.country_list = pd.read_csv(self.data_filepath + 'country_list.csv')['Country List']
        self.gdp_filepath = self.data_filepath + 'GDP/'
        self.climate_filepath = self.data_filepath + 'CLIMATE/'
        self.electricity_filepath = self.data_filepath + 'ELECTRICITY/'
        self.country_estimates_filepath = self.electricity_filepath + 'country_estimates/'
        self.external_project_filepath = '/Volumes/Hamish_ext/Mitigation_project'
        self.processed_load_filepath = self.external_project_filepath + '/Processed_Load/Annual_Hourly_Load_By_Village_Tier_Dwelling/'
        self.clover_load_filepath = self.external_project_filepath + '/CLOVER_inputs/Load/Load_by_year/'

    def build_annual_clover_profiles(self):

        # Set countries (for all use file)
        country_list = ['Angola', 'Benin']
        # country_list = self.country_list

        # Set Tiers of access annual per household values in kWh
        tiers = [0, 4.38, 73.0, 365.0, 1241.0, 2993.0]

        # Set household size
        hh_size = 5

        # Set community size, number of households
        community_size = 100

        # Set file directories (add as needed)
        # country_filepath = self.country_estimates_filepath

        # Iterate over countries
        for country in country_list:
            country_annual_values = pd.read_csv(self.country_estimates_filepath + country + '.csv')
            # print(country_annual_values)
            print(country)
            # Iterate over years
            for year in range(2020, 2051):
                print(year)
                # select year value and calculate target value for total community
                year_value = country_annual_values[str(year)].values
                household_value = year_value * hh_size
                target_value = year_value * hh_size * community_size
                # print(target_value)

                # Get closest tiers to target value (METHOD 1)
                closest_tiers = build_inputs.find_closest_tier(self, tiers, household_value)

                # Get tier shares for target value (METHOD 2)
                # tier_shares, closest_tiers = build_inputs.return_tier_shares(self, household_value, tiers)
                # print(tier_shares, closest_tiers)

                # Create empty profile to add to and total value for while loop
                country_year_profile = np.zeros(8760)
                sum_value = 0
                household_count = 0

                # While loop that continues until the sum value reaches target value
                while sum_value < target_value:

                    # Select random number between 1 and 25, 25 household profiles used
                    household_number = np.random.randint(1, 26)

                    # Select random number between 1 and 3, array of closest tiers [1, 2, 3]
                    tier_number = np.random.randint(0, 3)
                    tier = closest_tiers[tier_number]

                    # Pull in respective annual load profile for household, tier and country (converted to kWh)
                    load = (pd.read_csv(self.processed_load_filepath + country + '_Tier' + str(tier) + '_dwelling' +
                                        str(household_number) + '_annual_hourly.csv')['load'].values)/1000

                    # Add up load values to give annual figure
                    annual_load = np.sum(load)
                    sum_value += annual_load
                    country_year_profile += (load * 1000)  # Add load to total, watt hours
                    household_count += 1

                country_year_profile = pd.DataFrame([country_year_profile]).T
                country_year_profile.columns = [str(year)]
                country_year_profile.to_csv(self.clover_load_filepath + country + '_community_load_' + str(year)
                                            + '.csv')
                print(country_year_profile)


    # Method 1 - Random Values
    def find_closest_tier(self, tiers, value):
        tier_value = min(tiers,key=lambda x:abs(x-value))
        tier = tiers.index(tier_value)
        if tier == 1:
            closest_tiers = [1, 1, 2]
        if tier == 5:
            closest_tiers = [4, 5, 5]
        else:
            closest_tiers = [tier-1, tier, tier+1]
        return closest_tiers

    # Method 2 - Tier Shares
    # def return_tier_shares(self, household_value, tiers):
    #
    #     tier_value = min(tiers, key=lambda x: abs(x - household_value))
    #     tier = tiers.index(tier_value)
    #     if tier_value == 1:
    #         closest_tiers = [1, 2]
    #     if tier == 5:
    #         closest_tiers = [4, 5]
    #     else:
    #         closest_tiers = [tier-1, tier, tier+1]
    #         # find which tiers values sit between
    #
    #     print(tier_value, tier, household_value)
    #     closest_tiers = [1, 2]
    #     tier_shares = [40, 60]
    #     return tier_shares, closest_tiers






build_inputs().build_annual_clover_profiles()




