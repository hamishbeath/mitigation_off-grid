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


class BuildInputs:
    def __init__(self):
        self.data_filepath = '~/Library/Mobile Documents/com~apple~CloudDocs/Mitigation_project/DATA/'
        self.country_list_all = pd.read_csv(self.data_filepath + 'country_list.csv')
        self.country_list_select = pd.read_csv(self.data_filepath + 'country_list.csv')['Country List']
        self.region_quintile_list = pd.read_csv(self.data_filepath + 'quintile_regions.csv')
        self.gdp_filepath = self.data_filepath + 'GDP/'
        self.climate_filepath = self.data_filepath + 'CLIMATE/'
        self.electricity_filepath = self.data_filepath + 'ELECTRICITY/'
        self.country_estimates_filepath = self.electricity_filepath + 'country_estimates/'
        self.external_project_filepath = '/Volumes/Hamish_ext/Mitigation_project'
        self.processed_load_filepath = self.external_project_filepath + '/Processed_Load/Annual_Hourly_Load_By_' \
                                                                        'Village_Tier_Dwelling/'
        self.clover_load_filepath = self.external_project_filepath + '/CLOVER_inputs/Load/Load_by_year/'

    def build_annual_clover_profiles(self):

        # Set countries (for all use file)
        # country_list = ['Angola', 'Benin', 'Bangladesh', 'DRC', 'South Africa']
        country_list = self.country_list_select

        # Set Tiers of access annual per household values in kWh
        tiers = [0, 4.5, 73.0, 365.0, 1250.0, 3000.0]
        hh_size = 4.5  # Set household size
        community_size = 100  # Set community size, number of households

        # Iterate over countries
        for country in country_list:
            country_annual_values = pd.read_csv(self.country_estimates_filepath + country + '.csv')
            country_quintile_share = BuildInputs.get_lowest_quintile_share(self, country, self.country_list_all,
                                                                           self.region_quintile_list)
            print(country)
            # Iterate over years
            for year in range(2020, 2051):

                # select year value for lowest income quintile and calculate target value for total community
                year_value = country_annual_values[str(year)].values * country_quintile_share  # kWh
                household_value = int(year_value * hh_size)  # kWh
                # target_value = year_value * hh_size * community_size

                # Get the relevant shares for closest tiers to the household value
                tier_shares = BuildInputs.return_tier_shares(self, household_value, tiers)
                print(tier_shares)

                # Create empty profile to add households to
                country_year_profile = np.zeros(8760)

                # Distinguish between normal and exception cases (above tier 5 or below tier 1)
                if len(tier_shares) == 1:  # Exception cases
                    single_tier = tier_shares[0]
                    single_tier = single_tier[0]

                    # Add in 100 relevant tier households, randomised
                    for i in range(0, 100):
                        household_number = np.random.randint(1, 26)
                        load = pd.read_csv(self.processed_load_filepath + country + '_Tier' + str(single_tier) + '_dwelling' +
                                                 str(household_number) + '_annual_hourly.csv')['load'].values  # Wh
                        country_year_profile += load

                    # Increase or decrease profiles by relevant factor
                    if single_tier == 5:
                        country_year_profile = country_year_profile * (household_value / tiers[5])
                    elif single_tier == 1:
                        country_year_profile = country_year_profile * (household_value / tiers[1])

                else:   # Normal cases
                    lower_tier, upper_tier = tier_shares[0][0], tier_shares[1][0]
                    lower_share = int(tier_shares[0][1] * 100)
                    upper_share = int(tier_shares[1][1] * 100)

                    # Add in relevant percentage of lower tier households, randomised
                    for i in range(0, lower_share):
                        household_number = np.random.randint(1, 26)
                        lower_load = pd.read_csv(self.processed_load_filepath + country + '_Tier' + str(lower_tier) + '_dwelling' +
                                                 str(household_number) + '_annual_hourly.csv')['load'].values  # Wh
                        country_year_profile += lower_load

                    # Add in relevant percentage of upper tier households, randomised
                    for j in range(0, upper_share):
                        household_number = np.random.randint(1, 26)
                        upper_load = pd.read_csv(self.processed_load_filepath + country + '_Tier' + str(upper_tier) +
                                                 '_dwelling' + str(household_number) + '_annual_hourly.csv')['load'].values # Wh
                        country_year_profile += upper_load

                # Export country year demand profile to drive
                country_year_profile = pd.DataFrame([country_year_profile]).T
                country_year_profile.columns = [str(year)]
                country_year_profile.to_csv(self.clover_load_filepath + country + '_community_load_' + str(year)
                                            + '.csv')  # Wh

    # Function that gets the proportion of electricity demanded by lowest quintile, by region
    def get_lowest_quintile_share(self, country, country_list, region_list):

        # Extract country region from list
        country_list = country_list.set_index('Country List')
        country_value = country_list['Region'][country]

        # Extract relevant region quintile value
        region_list = region_list.set_index('Region')
        quintile_value = region_list['Quintile Share'][country_value]
        return quintile_value

    # Function that calculates the relevant shares of electricity access demands tiers are required
    def return_tier_shares(self, household_value, tiers):

        # Retrieve closest tier value and tier of access to household value
        closest_tier_value = min(tiers, key=lambda x: abs(x - household_value))
        closest_tier = tiers.index(closest_tier_value)

        # Calculate relevant 'sandwich' tier(s) to include in demand profile
        if closest_tier_value <= household_value:
            if closest_tier == 5:
                sandwich_tiers = [5]  # If the household value is higher than tier 5, different conditions apply
            else:
                sandwich_tiers = [closest_tier, closest_tier + 1]
        elif closest_tier_value > household_value:
            if closest_tier == 1:
                sandwich_tiers = [1]  # If the household value is lower than tier 1, different conditions apply
            else:
                sandwich_tiers = [closest_tier - 1, closest_tier]
        # print('sandwich tiers', sandwich_tiers)
        # Calculate share of each sandwich tier
        if len(sandwich_tiers) == 1:  # This takes the special cases out of the equation and keeps len at 1
            tier_shares = [sandwich_tiers]
        else:
            lower_tier, upper_tier = sandwich_tiers[0], sandwich_tiers[1]
            zeroed_upper = tiers[upper_tier] - tiers[lower_tier]
            zeroed_household_value = household_value - tiers[lower_tier]
            tier_percentage_value = zeroed_household_value / zeroed_upper
            tier_shares = [[lower_tier, 1-tier_percentage_value], [upper_tier, tier_percentage_value]]

        return tier_shares

BuildInputs().build_annual_clover_profiles()
